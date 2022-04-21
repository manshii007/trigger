from django.dispatch import receiver
from django.db.models import Q
from django.db.models.signals import post_save, m2m_changed
from sklearn.multiclass import OneVsOneClassifier
from .tasks import move_file
from notifications.signals import notify
from django.core.mail import send_mail, EmailMessage
import uuid
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from rest_framework_simplejwt.tokens import RefreshToken
from guardian.shortcuts import assign_perm

from .models import (
    File,
    Folder,
    Movie,
    ProjectVersion,
    Projects,
    Series,
    Channel,
    ChannelClip,
    WorkFlowInstance,
    WorkFlowStage,
    WorkFlowInstanceStep,
    WorkFlowInstanceMembership,
    WorkFlowStep,
    WorkGroup,
    AssetVersion,
    WorkFlowCollectionInstance,
    WorkFlowCollectionInstanceStep,
    Collection,
    Demo,
    DemoOTP
)
from video.models import Video
from users.models import User
from video.tasks import index_faces_azure, index_emotions_azure, index_locations, index_shots
import logging, sys

from workgroups.models import *

LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO'
    }
}
logging.config.dictConfig(LOGGING)


# @receiver(signal=post_save, sender=Movie)
# def create_folder_for_movie(sender, instance, **kwargs):
#     if kwargs.get('created'):
#         print("movie asset created")
#         create_folder.delay("Movie_{}".format(instance.movie_title))
#         instance.channel = Channel.objects.get(channel_name='Colors')
#         instance.save()
#
#
# @receiver(signal=post_save, sender=Series)
# def create_folder_for_series(sender, instance, **kwargs):
#     if kwargs.get('created'):
#         print("series asset created")
#         create_folder.delay("TVSeries_{}".format(instance.series_title))

@receiver(signal=post_save, sender=ChannelClip)
def channel_clip_created_get_fingerprint(sender, instance, **kwargs):
    if kwargs.get('created'):
        print("Channel Clip Created")
        # get_fingerprint.delay(instance.id)


@receiver(post_save, sender=WorkFlowInstance)
def generate_work_flow_instance_steps(sender, created, instance, **kwargs):
    if created:
        qs = WorkFlowStage.objects.filter(work_flow=instance.work_flow)
        stage = qs.filter(prev_step=None).first()
        next_step = stage.next_step
        obj_list = []

        # while next_step != None:
        #     obj = WorkFlowInstanceStep(work_flow_instance=instance, work_flow_step=next_step, work_flow_step_status="NSD")
        #     obj_list.append(obj)
        #     stage = qs.filter(prev_step=next_step).first()
        #     next_step = stage.next_step

        # WorkFlowInstanceStep.objects.bulk_create(obj_list)
        while next_step != None:
            obj = WorkFlowInstanceStep.objects.create(work_flow_instance=instance, work_flow_step=next_step,
                                                      work_flow_step_status="NSD")
            stage = qs.filter(prev_step=next_step).first()
            if stage:
                next_step = stage.next_step
            else:
                break


# A workflowinstancemembership object is created whenever an asset version is added to a workflow instance
@receiver(post_save, sender=WorkFlowInstanceMembership)
def work_flow_instance_changed(sender, instance, **kwargs):
    if kwargs.get("created"):
        # In Songs workflow, whenever a new intermediate proxy is added as a asset version change the programming step to review and editing to not started
        # In Songs workflow and SpotboyE, whenever a new master proxy is added as a asset version change the master proxy upload step to completed
        if instance.work_flow_instance.work_flow.title == "Songs Workflow" or instance.work_flow_instance.work_flow.title == "SpotboyE Workflow":
            if instance.asset_version.proxy_type == "ITM":
                programming = WorkFlowInstanceStep.objects.filter(work_flow_instance=instance.work_flow_instance,
                                                                  work_flow_step__title="Programming").first()
                if programming:
                    programming.work_flow_step_status = "REV"
                    programming.save()

                editing = WorkFlowInstanceStep.objects.filter(work_flow_instance=instance.work_flow_instance,
                                                              work_flow_step__title="Editing").first()
                if editing:
                    editing.work_flow_step_status = "NSD"
                    editing.save()
            if instance.asset_version.proxy_type == "MTR":
                master_proxy_upload = WorkFlowInstanceStep.objects.filter(
                    work_flow_instance=instance.work_flow_instance, work_flow_step__title="Master Proxy Upload").first()
                if master_proxy_upload:
                    master_proxy_upload.work_flow_step_status = "CMP"
                    master_proxy_upload.save()


def get_status(status):
    status_choices = {
        'NSD': 'Not Started',
        'REV': 'Review',
        'APR': 'Approve',
        'APE': 'Approve with Edits',
        'REJ': 'Reject',
        'CMP': 'Completed',
        'FAI': 'Failed',
        'PAS': 'Pass',
        'OVE': 'Override'
    }
    return status_choices[status]


def notify_users(instance):
    work_flow = instance.work_flow_instance.work_flow
    title = instance.work_flow_step.title
    status = instance.work_flow_step_status
    work_flow_instance = instance.work_flow_instance

    qs = WorkFlowStage.objects.filter(work_flow=work_flow)
    stage = qs.filter(prev_step=None).first()
    next_step = stage.next_step
    workgroup_list = []

    while next_step != None:
        obj = WorkFlowStep.objects.filter(id=next_step.id).first()
        workgroup_list.append(obj.workgroup)
        stage = qs.filter(prev_step=next_step).first()
        next_step = stage.next_step

    modified_by = WorkFlowInstanceStep.objects.filter(id=instance.id).first()
    if modified_by.modified_by:
        sender = User.objects.filter(id=modified_by.modified_by.id).first()
        users_all = []
        for workgroup in workgroup_list:
            if workgroup:
                users = WorkGroup.objects.filter(id=workgroup.id).values_list("members__user", flat=True)
                users = list(User.objects.filter(id__in=users))
                users_all = users_all + users
        asset_title = AssetVersion.objects.filter(work_flow_instances=work_flow_instance,
                                                  proxy_type="SRC").first().title
        status = get_status(status)
        notifications = notify.send(sender=sender, recipient=users_all,
                                    verb='<b>{} {}</b> changed {} to {} in <b>{}</b>'.format(sender.first_name,
                                                                                             sender.last_name, title,
                                                                                             status, asset_title))


@receiver(post_save, sender=WorkFlowInstanceStep)
def work_flow_logic(sender, instance, **kwargs):
    if not kwargs.get("created"):
        notify_users(instance)
        if instance.work_flow_instance.work_flow.title == "Songs Workflow" or instance.work_flow_instance.work_flow.title == "Elements Workflow":
            if instance.work_flow_step.title == "Programming":
                # if programming is changed to approve, change editing to completed
                if instance.work_flow_step_status == "APR":
                    editing = WorkFlowInstanceStep.objects.filter(work_flow_instance=instance.work_flow_instance,
                                                                  work_flow_step__title="Editing").first()
                    if editing:
                        editing.work_flow_step_status = "CMP"
                        editing.save()
                elif instance.work_flow_step_status == "APE":
                    # if programming is changed to approve with edits, change editing to review
                    editing = WorkFlowInstanceStep.objects.filter(work_flow_instance=instance.work_flow_instance,
                                                                  work_flow_step__title="Editing").first()
                    if editing:
                        editing.work_flow_step_status = "REV"
                        editing.save()
        if instance.work_flow_instance.work_flow.title == "Elements Workflow":
            if instance.work_flow_step.title == "Rough Cut":
                # if rough cut is changed to completed, change First Cut to Review
                if instance.work_flow_step_status == "CMP":
                    first_cut = WorkFlowInstanceStep.objects.filter(work_flow_instance=instance.work_flow_instance,
                                                                    work_flow_step__title="First Cut").first()
                    if first_cut:
                        first_cut.work_flow_step_status = "REV"
                        first_cut.save()
        if instance.work_flow_instance.work_flow.title == 'Manual Ingest Workflow':
            dest = '/data'
            if instance.work_flow_step.title == "QC":
                if instance.work_flow_step_status == "REJ":
                    print(instance.work_flow_step_status)
                    dest = '/data/QC_REJECT'
                elif instance.work_flow_step_status == "APR":
                    print(instance.work_flow_step_status)
                    dest = '/data/QC_APPROVED'
                elif instance.work_flow_step_status == "REV":
                    print(instance.work_flow_step_status)
                    dest = '/data/QC_REVIEW'
                elif instance.work_flow_step_status == "OVE":
                    print(instance.work_flow_step_status)
                    dest = '/data/QC_OVERIDE'
            elif instance.work_flow_step.title == "Water  Marking":
                if instance.work_flow_step_status == "NSD":
                    print(instance.work_flow_step_status)
                    dest = '/data/WM_NOTSTARTED'
                elif instance.work_flow_step_status == "CMP":
                    print(instance.work_flow_step_status)
                    dest = '/data/WM_COMPLETED'
                elif instance.work_flow_step_status == "REV":
                    print(instance.work_flow_step_status)
                    dest = '/data/WM_REVIEW'
                elif instance.work_flow_step_status == "OVE":
                    print(instance.work_flow_step_status)
                    dest = '/data/WM_OVERIDE'
            file_path = instance.work_flow_instance.asset_version.all()[0].notes
            move_file.delay(file_path, dest)

    elif kwargs.get("created"):
        if instance.work_flow_instance.work_flow.title == "Songs Workflow" or instance.work_flow_instance.work_flow.title == "SpotboyE Workflow":
            # change source QC to completed when Source QC step is created
            # logging.info(instance.work_flow_step.title)
            if instance.work_flow_step.title == "Source QC":
                instance.work_flow_step_status = "PAS"
                instance.save()


@receiver(post_save, sender=WorkFlowCollectionInstance)
def generate_work_flow_collection_instance_steps(sender, instance, **kwargs):
    if kwargs.get("created"):
        qs = WorkFlowStage.objects.filter(work_flow=instance.work_flow)
        stage = qs.filter(prev_step=None).first()
        next_step = stage.next_step
        obj_list = []

        while next_step != None:
            obj = WorkFlowCollectionInstanceStep.objects.create(work_flow_instance=instance, work_flow_step=next_step,
                                                                work_flow_step_status="NSD")
            stage = qs.filter(prev_step=next_step).first()
            next_step = stage.next_step


@receiver(post_save, sender=WorkFlowCollectionInstanceStep)
def work_flow_collection_logic(sender, instance, **kwargs):
    if not kwargs.get("created"):
        # notify_users(instance)
        if instance.work_flow_instance.work_flow.title == "Elements Workflow":
            if instance.work_flow_step.title == "Programming":
                # if programming is changed to approve, change editing to completed
                if instance.work_flow_step_status == "APR":
                    editing = WorkFlowCollectionInstanceStep.objects.filter(
                        work_flow_instance=instance.work_flow_instance, work_flow_step__title="Editing").first()
                    if editing:
                        editing.work_flow_step_status = "CMP"
                        editing.save()
                elif instance.work_flow_step_status == "APE":
                    # if programming is changed to approve with edits, change editing to review
                    editing = WorkFlowCollectionInstanceStep.objects.filter(
                        work_flow_instance=instance.work_flow_instance, work_flow_step__title="Editing").first()
                    if editing:
                        editing.work_flow_step_status = "REV"
                        editing.save()
            if instance.work_flow_step.title == "Rough Cut":
                # if rough cut is changed to completed, change First Cut to Review
                if instance.work_flow_step_status == "CMP":
                    first_cut = WorkFlowCollectionInstanceStep.objects.filter(
                        work_flow_instance=instance.work_flow_instance, work_flow_step__title="First Cut").first()
                    if first_cut:
                        first_cut.work_flow_step_status = "REV"
                        first_cut.save()


@receiver(post_save, sender=Collection)
def update_workflow_collection_step(sender, instance, **kwargs):
    if not kwargs.get("created"):
        # logging.info(instance)
        # filter(lambda x: x.work_flow.title == "Elements Workflow", work_flow_instances)
        workflows = instance.work_flow_instances.values_list("work_flow__title", "id")
        work_flow_instaces = [str(i[1]) for i in workflows if i[
            0] == "Elements Workflow"]  # workflows is a tuple containing (workflowtitle,workflowinstancesid)
        if len(work_flow_instaces) == 1:
            work_flow_instace = work_flow_instaces[0]
            asset_version = AssetVersion.objects.filter(collection=instance, proxy_type="ITM")
            if len(asset_version) == 1:
                first_cut = WorkFlowCollectionInstanceStep.objects.filter(work_flow_instance=work_flow_instace,
                                                                          work_flow_step__title="First Cut").first()
                if first_cut:
                    first_cut.work_flow_step_status = "CMP"
                    first_cut.save()
                programming = WorkFlowCollectionInstanceStep.objects.filter(work_flow_instance=work_flow_instace,
                                                                            work_flow_step__title="Programming").first()
                if programming:
                    programming.work_flow_step_status = "REV"
                    programming.save()
            asset_version = AssetVersion.objects.filter(collection=instance, proxy_type="MTR")
            if len(asset_version) >= 1:
                master_proxy_upload = WorkFlowCollectionInstanceStep.objects.filter(
                    work_flow_instance=work_flow_instace, work_flow_step__title="Master Proxy Upload").first()
                if master_proxy_upload:
                    master_proxy_upload.work_flow_step_status = "CMP"
                    master_proxy_upload.save()


@receiver(post_save, sender=User)
def demo_request_email(sender, instance, **kwargs):
    if kwargs.get("created"):
        # assign permissions
        t=Team.objects.create(name=instance.username+str(instance.id), owner=instance)
        t.user.add(instance)
        g,c=Group.objects.get_or_create(name=instance.username+str(instance.id))
        team_perms = [
            "team_view_file", "team_change_file", "team_delete_file",
            "team_view_folder", "team_change_folder", "team_delete_folder",
        ]
        perms = Permission.objects.filter(codename__in=team_perms)
        g.permissions.set(list(perms))
        g.user_set.add(instance)
        t.group.add(g)
        message = Mail(from_email='Tessact Support <no-reply@tessact.com>', to_emails=[instance.email])
        refresh = RefreshToken.for_user(instance)
        message.dynamic_template_data = {
            "auth_token": str(refresh),
            "username": instance.first_name
        }
        message.template_id = "d-4b5f7a1c32a74fc89975ba68ef33f7a6"
        try:
            sg = SendGridAPIClient("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")
            response = sg.send(message)
        except Exception as e:
            print("Error: {0}".format(e))

def index_videos(sender, instance, **kwargs):
    if instance.is_tagged == True:
        video_id = str(instance.video.id)
        index_faces_azure.delay(video_id)
        index_emotions_azure.delay(video_id)
        index_locations.delay(video_id)
        index_shots.delay(video_id)

def get_token(username, password, url):
    resp = requests.post(url, data={"username": username, "password": password})
    token = ""
    try:
        resp = resp.json()
        token = resp.get("auth_token", "")
    except:
        print("Bad request")
    print(token)
    return token

folder_metadata = {
    'Movies': {
        'Title Tab': {'Movie Title': None, 'AKA Titles': None, 'Year': None, 'Movie id': None, 'Production number': None, 'Channel Group':None, 'Production House':None, 'Keywords':None},
        'General Tab': {'Status': None, 'Type': None, 'Production': None, 'Certification': None, 'Maker': None, 'Classification':None, 'Languages':None, 'Slot duration':None, 'Orig.Duration':None, 'TX Run time':None, 'Content':None, 'External Ref. No.':None, 'Prod. Year':None, 'Classification':None, 'Barcode':None, 'TX ID':None},
        'Synopsis Tab': {'Long Synopsis':None, 'Short Synopsis':None},
        'Cast and Credits Tab':{'Rank':None, 'Artist':None, 'Role':None, 'Part Desc':None}
    },
    'Song': {
        'Title Tab': {'Song Title': None, 'AKA Titles': None, 'Year': None, 'Song id': None, 'Album Name': None, 'Channel Group':None, 'Production House':None, 'Keywords':None},
        'General Tab': {'Status': None, 'Type': None, 'Production': None, 'Certification': None, 'Maker': None, 'Classification':None, 'Languages':None, 'Slot duration':None, 'Orig.Duration':None, 'TX Run time':None, 'External Ref. No.':None, 'Prod. Year':None, 'Classification':None, 'Barcode':None, 'TX ID':None},
        'Cast and Credits Tab':{'Rank':None, 'Artist':None, 'Role':None, 'Part Desc':None}
    },
    'Promos': {
        'Title Tab': {'Promotion Title': None, 'AKA Titles': None, 'Channel Group': None, 'Certification': None, 'Producer': None, 'Unpackaged Master': None, 'Timecode In': None, 'Notes': None, 'Genre': None, 'Seq': None}
    },
    'Commercial': {
        'Title Tab': {'Commercial Title': None, 'AKA Titles': None, 'Production Number': None, 'Channel Group': None, 'House number': None, 'Product Code': None}
    }, 
    'TV-Series': {
        'Title Tab': {'Programme Title': None, 'AKA Titles': None, 'Series No.': None, 'Year': None, 'Programme Id': None, 'Production Number': None, 'Channel Group': None, 'Programme Group': None, 'Compilation': None},
        'General Tab': {'Status': None, 'Type': None, 'Production': None, 'Certification': None, 'Maker': None, 'Classification': None, 'No. of Episodes': None, 'Genre': None, 'seq': None,  'Languages': None, 'Slot Duration': None, 'Orig. Duration': None, 'TX Run Time': None, 'TX Order': None, 'Content': None, 'External Ref. No.': None, 'Barcode': None, 'TX ID': None},
        'Synopsis Tab': {'Long Synopsis': None, 'Short Synopsis': None}, 
        'Cast and Credits Tab': {'Rank': None, 'Artist': None, 'Role': None, 'Part Desc': None}
    }
}
file_metadata = {
    'Movies': {
        'Title Tab': {'Movie Title': None, 'AKA Titles': None, 'Version Title': None, 'Version Code': None, 'TX Order': None, 'Keywords':None},
        'General Tab': {'Status': None, 'Work List Status': None, 'External Reference': None, 'Classification': None, 'Certification': None, 'Aspect Ratio':None, 'Languages':None, 'Slot duration':None, 'TX Run time':None, 'TX Parts':None, 'TX Approved Timings':None, 'Description':None, 'Barcode':None, 'TX ID':None},
        'Technical Metadata Tab': {'Material Identifier -- Y':None, 'Compliance Status (With View Compliance Report Option)':None, 'Material Ref Id -- Y': None, 'Format -- Y(Preview Window)': None, 'Wrapper': None, 'Material Dur': None, 'Codec -- Y': None, 'Aspect Ratio': None, 'Bitrate -- Y': None, 'Bitrate Mode -- Y': None, 'Frame Rate -- Y(Preview Window)': None, 'Display Resolution -- Y': None},
        'Audio Tab': {'Track ( 1, 2, 3 …) -- Y':None, 'Name (example: Hindi, english etc) -- Y':None, 'Available (yes/no) -- Y':None},
        'Subtitles/CC Tab': {'Serial No. -- Y': None, 'Language -- Y': None, 'Available (Yes/No) -- Y': None},
        'End Credits Tab': {'Start time': None, 'End time': None, 'Voice in EC (yes/no)': None}
    },
    'Songs': {
        'Title Tab': {'Song Title': None, 'AKA Titles': None, 'Version Title': None, 'Version Code':None, 'Album Name': None, 'Channel Group': None, 'Production House': None, 'Duration': None, 'Keywords': None},
        'General Tab': {'Status': None, 'Work List Status': None, 'External Reference': None, 'Classification': None, 'Certification': None, 'Aspect Ratio':None, 'Languages':None, 'Slot duration':None, 'TX Run time':None, 'TX Parts':None, 'TX Approved Timings':None, 'Prod. Year':None, 'Description':None, 'Barcode':None, 'TX ID':None},
    },
    'Promos': {
        'Title Tab': {'Promotion Title': None, 'AKA Titles': None, 'Channel Group': None, 'Version Type': None, 'Version Title': None, 'Dublist Export Date': None, 'Event Type': None, 'Production Number': None, 'House Number': None, 'Keywords': None},
        'General Tab': {'Duration': None, 'Priority': None, 'Certification': None, 'Created for Month': None, 'Created for Year':None, 'Producer':None, 'Notes':None},
        'Usage Tab': {'Valid Dates From':None, 'Valid Dates To':None, 'Valid Days': None, 'Programme/Episode': None, 'Planned Tx Date/Time': None, 'Channel': None},
        'Technical Metadata Tab':{'Material Identifier -- Y':None, 'Compliance Status (With View Compliance Report Option)':None, 'Material Ref Id -- Y':None, 'Format -- Y(Preview Window)':None, 'Wrapper': None, 'Material Dur':None, 'Codec -- Y': None, 'Aspect Ratio': None, 'Bitrate -- Y': None, 'Bitrate Mode -- Y': None, 'Frame Rate -- Y(Preview Window)': None, 'Display Resolution -- Y': None},
        'Audio Tab': {'Track ( 1, 2, 3 …) -- Y': None, 'Name (example: Hindi, english etc) -- Y': None, 'Available (yes/no) -- Y': None}, 
        'Subtitles/CC Tab': {'Serial No. -- Y': None, 'Language -- Y': None, 'Available (Yes/No) -- Y': None}
    },
    'Commercial': {
        'Title Tab': {'Commercial Title': None, 'Version Title': None, 'Production Number': None, 'Channel Group': None, 'House Number': None, 'Dublist Export Date': None, 'Product code': None, 'Keywords': None},
        'General Tab': {'Duration': None, 'Certification': None, 'Estimated First Air Date': None, 'Expiry Date': None},
        'Comments Tab': {'Comments':None},
        'Technical Metadata Tab':{'Material Identifier -- Y':None, 'Compliance Status (With View Compliance Report Option)':None, 'Material Ref Id -- Y':None, 'Format -- Y(Preview Window)':None, 'Wrapper': None, 'Material Dur':None, 'Codec -- Y': None, 'Aspect Ratio': None, 'Bitrate -- Y': None, 'Bitrate Mode -- Y': None, 'Frame Rate -- Y(Preview Window)': None, 'Display Resolution -- Y': None},
        'Audio Tab': {'Track ( 1, 2, 3 …) -- Y': None, 'Name (example: Hindi, english etc) -- Y': None, 'Available (yes/no) -- Y': None}, 
        'Subtitles/CC Tab': {'Serial No. -- Y': None, 'Language -- Y': None, 'Available (Yes/No) -- Y': None}
    },
    'TV-Series': {
        'Title Tab': {'Programme Title': None, 'AKA Titles': None, 'Series No.': None, 'Episode No.': None, 'Episode Title': None, 'Version Title': None, 'Version Code': None, 'TX Order': None, 'Keywords': None},
        'General Tab': {'Status': None, 'Work List Status': None, 'External Refernce': None, 'Classification': None, 'Certification':None, 'Aspect Ratio':None, 'Languages':None, 'Lock Segments Within The Same Part': None, 'Slot Duration': None, 'TX Run Time':None, 'TX Parts':None, 'TX Approved Timings':None, 'Part': None, 'Description': None, 'Barcode': None, 'TX ID': None},
        'Technical Metadata Tab':{'Material Identifier -- Y':None, 'Compliance Status (With View Compliance Report Option)':None, 'Material Ref Id -- Y':None, 'Format -- Y(Preview Window)':None, 'Wrapper': None, 'Material Dur':None, 'Codec -- Y': None, 'Aspect Ratio': None, 'Bitrate -- Y': None, 'Bitrate Mode -- Y': None, 'Frame Rate -- Y(Preview Window)': None, 'Display Resolution -- Y': None},
        'Audio Tab': {'Track ( 1, 2, 3 …) -- Y': None, 'Name (example: Hindi, english etc) -- Y': None, 'Available (yes/no) -- Y': None}, 
        'Subtitles/CC Tab': {'Serial No. -- Y': None, 'Language -- Y': None, 'Available (Yes/No) -- Y': None},
        'End Credits': {'Start time': None, 'End time': None, 'Voice in EC(yes/no)': None}
    },
}


def set_file_folder_metadata(instance_id):
    instance = File.objects.get(id=instance_id)
    parent_folder = instance.location
    category = parent_folder.category.title if parent_folder.category is not None else None
    if category in folder_metadata.keys() and not parent_folder.title_metadata:
        parent_folder.title_metadata = folder_metadata[category]
        parent_folder.title_metadata['Title Tab']['Movie Title'] = instance.title
        parent_folder.save()
    if category in file_metadata.keys():
        instance.file_metadata = file_metadata[category]
        instance.file_metadata['Title Tab']['Movie Title'] = instance.title
        instance.save()



@receiver(post_save, sender=File)
def create_file(sender, instance, created, **kwargs):
    if created:
        # create & save video, image or pdf file objects
        if instance.type == "video":
            v = Video.objects.create(title=instance.title, file=instance.url)
            instance.video_id = v.id
            instance.save()
            set_file_folder_metadata(instance.id)
        elif instance.type == "image":
            # create image here
            print("image")


@receiver(post_save, sender=Projects)
def create_project_version(sender, instance, created, **kwargs):
    if created:
        if instance.workflow:
            workflow_instance = WorkFlowInstance.objects.create(work_flow=instance.workflow)
            project_version = ProjectVersion.objects.create(project=instance, version_number=1, workflow_instance=workflow_instance)
        else:
            project_version = ProjectVersion.objects.create(project=instance, version_number=1)
        if instance.created_by:
            user=instance.created_by
            assign_perm('view_projectversion', user, project_version)
            assign_perm('change_projectversion', user, project_version)
            assign_perm('delete_projectversion', user, project_version)
