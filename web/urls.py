from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.core.urlresolvers import reverse_lazy
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import RedirectView
from authentication.views import AuthOTPViewSet, TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from rest_framework.documentation import include_docs_urls

from content.views import ProjectMetadataViewset, WorkFlowMetadataViewset, aws_uploadid, aws_presigned_url, aws_complete, library, librarysearch, generate_report, library_delete

from rest_framework_nested import routers

from assets.views import (
    ROViewSet,
)
from users.views import (
    UserViewSet,
    HealthCheck,
    UserPermissionsViewSet,
    ProfileViewSet,
    AllUserViewSet,
    JobUserViewSet,
    UpdatePasswordViewSet,
    ProfilePasswordViewSet,
    NotificationsViewSet,
    forgot_password
)
from workgroups.views import (
    WorkGroupViewSet,
    GroupViewSet,
    WorkGroupVideosViewSet,
    WorkGroupMembersViewSet,
    WorkGroupPermissionsViewSet,
    WorkGroupTaggingJobsViewSet,
    TeamViewSet,
    OrganizationViewSet,
    RoleViewSet,
    WorkGroupMembershipViewSet
)
from video.views import (
    SignedUrlViewershipViewset,
    VideoViewSet,
    VideoLibraryViewSet,
    AudioViewSet,
    TranscriptionViewSet,
    SubtitleViewSet,
    VideoProxyPathViewSet,
    ClipViewSet,
    TicketViewSet,
    CreateEndpointViewset,
    DeleteEndpointViewset,
    SetThumbnail
)
from tags.views import (
    CheckTagViewSet,
    CorrectionTagViewSet,
    TagViewSet,
    TagCategoryViewSet,
    FrameTagViewSet,
    SceneTagViewSet,
    KeywordTagViewSet,
    LogoTagViewSet,
    LogoViewSet,
    ComplianceStatusViewSet,
    BarcTagViewSet,
    ProgramGenreViewSet,
    ProgramThemeViewSet,
    AdvertiserGroupViewSet,
    AdvertiserViewSet,
    BrandCategoryViewSet,
    BrandSectorViewSet,
    BrandNameViewSet,
    TitleViewSet,
    DescriptorViewSet,
    SpecChannelViewSet,
    ChannelGenreViewSet,
    ChannelNetworkViewSet,
    RegionViewSet,
    ContentLanguageViewSet,
    ProductionHouseViewSet,
    PromoViewSet,
    ProgramViewSet,
    CommercialViewSet,
    PlayoutTagViewSet,
    SpriteTagViewSet,
    CommercialTagViewSet,
    TPromoViewSet,
    TProgramViewSet,
    TCommercialViewSet,
    PromoCategoryViewSet,
    GenericTagViewSet,
    ManualTagViewSet,
    ManualTagQCStatusViewSet,
    MarkerViewSet,
)
from content.views import (
    # GenericLibraryViewSet,
    FileViewSet,
    FolderViewSet,
    AdvancedSearchViewSet,
    CategoriesViewset,
    ChannelViewSet,
    PersonViewSet,
    CharacterViewSet,
    GenreViewSet,
    ContextTypeViewSet,
    SeriesViewSet,
    EpisodeViewSet,
    PoliticianViewSet,
    TVAnchorViewSet,
    MovieSegmentViewSet,
    MovieViewSet,
    EpisodeSegmentViewSet,
    TriviaViewSet,
    ActorViewSet,
    PersonGroupViewSet,
    PlaylistEntryViewSet,
    PlaylistViewSet,
    SongViewSet,
    TriviaLogViewSet,
    LabelViewSet,
    NxSongViewSet,
    InstaViewSet,
    NxMovieViewSet,
    NxPersonViewSet,
    PlaylistDate,
    TriviaEditLogViewSet,
    TriviaReviewLogViewSet,
    ChannelClipViewSet,
    BarcChannelsViewSet,
    SongVerificationViewSet,
    AssetVersionViewSet,
    CollectionViewSet,
    AssignWorkFlowInstanceStepViewSet,
    SegmentViewSet,
    RushesViewSet,
    ContentTypeViewSet,
    PromoViewSet,
    MetadataAudioViewSet,
    SongAssetViewSet,
    BatchViewSet,
    VideoProcessingStatusViewSet,
    SequenceViewSet,
    SeasonViewSet,
    WorkFlowViewSet,
    WorkFlowStepViewSet,
    WorkFlowInstanceViewSet,
    WorkFlowInstanceStepViewSet,
    WorkFlowStageViewSet,
    WorkFlowTransitionHistoryViewSet,
    WorkFlowCollectionInstanceViewSet,
    WorkFlowCollectionInstanceStepViewSet,
    AssignWorkFlowCollectionInstanceStepViewSet,
    CommercialAssetViewSet,
    DemoViewSet,
    ProjectFileViewset,
    ProjectVersionViewset,
    ProjectViewset
)
from content.views import PromoViewSet as VideoPromoViewSet
from permissions.views import (
    PermissionsViewSet
)
from comments.views import (
    CommentViewSet
)
from jobs.views import (
    TaggingJobViewSet,
    JobTypeViewSet,
    FrameJobViewSet,
    AutoVideoJobViewSet,
    SubtitleSyncJobViewSet,
    ScriptProcessViewSet,
    SubtitleTranslationJobViewSet,
    ReviewTranslationJobViewSet,
    MovieTranslationJobViewSet,
    EpisodeTranslationJobViewSet
)

from frames.views import (
    RectViewSet,
    FramesViewSet,
    VideoFrameViewSet,
    PersonFrameViewSet
)

from contextual.views import (
    FaceViewSet,
    FaceGroupViewSet,
    HardCutsViewSet,
)

from masters.views import (
    VendorReportViewSet,
    VendorViewSet,
    VendorMasterViewSet,
    SuperMasterViewSet,
    MasterReportViewSet,
    VendorCommercialViewSet,
    VendorPromoViewSet,
    VendorProgramViewSet,
    SuperCommercialViewSet,
    SuperPromoViewSet,
    SuperProgramViewSet,
    VendorMasterComparisonViewSet,
    StatViewSet,
    WeeklyReportViewSet,
    VendorContentLanguageViewset,
    VendorProgramGenreViewset,
    VendorPromoCategoryViewset,
    VendorChannelViewset
)

from publication.views import (
    PublicationViewSet
) 

from feedback.views import (
    FeedbackViewSet
    )

import notifications.urls


API_TITLE = 'API title'
API_DESCRIPTION = '...'
admin.site.site_header = "Trigger Admin"

router = DefaultRouter()
router.register(r'users', UserViewSet, base_name='users')
router.register(r'all_users', AllUserViewSet, base_name='allusers')
router.register(r'profile', ProfileViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'workgroups', WorkGroupViewSet, base_name='workgroups')
router.register(r'videos', VideoViewSet, base_name='video')
router.register(r'audios', AudioViewSet)
router.register(r'transcriptions', TranscriptionViewSet)
router.register(r'subtitles', SubtitleViewSet)
router.register(r'tags', TagViewSet)
router.register(r'frame_tags', FrameTagViewSet)
router.register(r'check_tags', CheckTagViewSet)
router.register(r'correction_tags', CorrectionTagViewSet)
router.register(r'keyword_tags', KeywordTagViewSet)
router.register(r'categories', CategoriesViewset)
router.register(r'markers', MarkerViewSet, base_name='markers')
router.register(r'files', FileViewSet, base_name='files')
router.register(r'folders', FolderViewSet, base_name='folders')
router.register(r'projects', ProjectViewset, base_name='projects')
router.register(r'project_versions', ProjectVersionViewset, base_name='project_versions')
router.register(r'project_files', ProjectFileViewset, base_name='project_files')
router.register(r'project_metadata', ProjectMetadataViewset)
router.register(r'workflow_metadata', WorkFlowMetadataViewset)
router.register(r'tags_categories', TagCategoryViewSet)
router.register(r'video_library', VideoLibraryViewSet)
router.register(r'permissions', PermissionsViewSet)
router.register(r'tagging_job', TaggingJobViewSet)
router.register(r'auto_video_jobs', AutoVideoJobViewSet)
router.register(r'job_type', JobTypeViewSet)
router.register(r'subtitle_sync_job', SubtitleSyncJobViewSet, base_name='subtitlesyncjob')
router.register(r'script_process_job', ScriptProcessViewSet, base_name='scriptprocessjob')
router.register(r'frames', FramesViewSet)
router.register(r'videoframes', VideoFrameViewSet)
router.register(r'framejobs', FrameJobViewSet, base_name='frame_job')
router.register(r'rect', RectViewSet)
router.register(r'scenes', SceneTagViewSet)
router.register(r'channels', ChannelViewSet)
router.register(r'persons', PersonViewSet)
router.register(r'characters', CharacterViewSet)
router.register(r'genre', GenreViewSet)
router.register(r'series', SeriesViewSet)
router.register(r'episodes', EpisodeViewSet)
router.register(r'context_type', ContextTypeViewSet)
router.register(r'faces', FaceViewSet)
router.register(r'facegroups', FaceGroupViewSet)
router.register(r'hardcuts', HardCutsViewSet)
router.register(r'politicians', PoliticianViewSet)
router.register(r'personframes', PersonFrameViewSet)
router.register(r'tvanchors', TVAnchorViewSet)
router.register(r'actor', ActorViewSet)
router.register(r'subtitle_translation_job', SubtitleTranslationJobViewSet, base_name="subtitletranslationjob")
router.register(r'review_translation_job', ReviewTranslationJobViewSet, base_name="reviewtranslationjob")
router.register(r'movies', MovieViewSet, base_name="movies" )
router.register(r'moviesegments', MovieSegmentViewSet)
router.register(r'episodesegments', EpisodeSegmentViewSet)
router.register(r'movie_translation_job', MovieTranslationJobViewSet, base_name="movietranslationjob")
router.register(r'trivia', TriviaViewSet, base_name="trivia")
router.register(r'persongroups', PersonGroupViewSet)
router.register(r'episode_translation_job', EpisodeTranslationJobViewSet, base_name="episodetranslationjob")
router.register(r'job_users', JobUserViewSet)
router.register(r'logo', LogoViewSet)
router.register(r'logo_tags', LogoTagViewSet)
router.register(r'ro', ROViewSet)
router.register(r'playlist', PlaylistViewSet)
router.register(r'playlist_entry', PlaylistEntryViewSet)
router.register(r'songs', SongViewSet)
router.register(r'trivia_logs', TriviaLogViewSet)
router.register(r'labels', LabelViewSet)
router.register(r'nxsongs', NxSongViewSet)
router.register(r'insta', InstaViewSet, base_name='insta')
router.register(r'nxmovies', NxMovieViewSet)
router.register(r'nxpersons', NxPersonViewSet)
router.register(r'playlist_date', PlaylistDate)
router.register(r'triviaeditlog', TriviaEditLogViewSet)
router.register(r'triviareviewlog',TriviaReviewLogViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'compliancestatustag', ComplianceStatusViewSet)
router.register(r'organizations', OrganizationViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'workgroups', WorkGroupViewSet)
router.register(r'barctags', BarcTagViewSet)
router.register(r'channelclips', ChannelClipViewSet)
router.register(r'barcchannels', BarcChannelsViewSet, base_name="barcchannel")
router.register(r'programtheme', ProgramThemeViewSet, base_name='programtheme')
router.register(r'programgenre', ProgramGenreViewSet, base_name="programgenre")
router.register(r'advertiser', AdvertiserViewSet, base_name="advertiser")
router.register(r'advertisergroup', AdvertiserGroupViewSet, base_name="advertisergroup")
router.register(r'brandname', BrandNameViewSet, base_name="brandname")
router.register(r'brandcategory', BrandCategoryViewSet, base_name="brandcategory")
router.register(r'brandsector', BrandSectorViewSet, base_name="brandsector")
router.register(r'title', TitleViewSet)
router.register(r'descriptor', DescriptorViewSet, base_name="descriptor")
router.register(r'promocategory', PromoCategoryViewSet)
router.register(r'specchannels', SpecChannelViewSet, base_name="specchannels")
router.register(r'channelgenres', ChannelGenreViewSet)
router.register(r'channelnetworks', ChannelNetworkViewSet)
router.register(r'regions', RegionViewSet)
router.register(r'contentlanguages', ContentLanguageViewSet)
router.register(r'productionhouses', ProductionHouseViewSet)
router.register(r'programs', ProgramViewSet)
router.register(r'promo', PromoViewSet)
router.register(r'commercials', CommercialViewSet)
router.register(r'playouttags', PlayoutTagViewSet)
router.register(r'sprite_tags', SpriteTagViewSet, base_name="spritetags")
router.register(r'commercial_tags', CommercialTagViewSet, base_name='commercialtags')
router.register(r'vendors', VendorViewSet)
router.register(r'vendormasters', VendorMasterViewSet)
router.register(r'vendorreports', VendorReportViewSet)
router.register(r'supermasters', SuperMasterViewSet)
router.register(r'weeklyreports', WeeklyReportViewSet)
router.register(r'masterreports', MasterReportViewSet)
router.register(r'tprograms', TProgramViewSet, base_name='tprograms')
router.register(r'tpromos', TPromoViewSet, base_name='tpromos')
router.register(r'tcommercials', TCommercialViewSet, base_name='tcommercials')
router.register(r'vendorcommercials', VendorCommercialViewSet)
router.register(r'vendorprogram', VendorProgramViewSet)
router.register(r'signedurls', SignedUrlViewershipViewset, base_name='signedurls')
router.register(r'vendorpromo', VendorPromoViewSet)
router.register(r'vendorchannels', VendorChannelViewset)
router.register(r'vendorpromocategory', VendorPromoCategoryViewset)
router.register(r'vendorcontentlanguage', VendorContentLanguageViewset)
router.register(r'vendorprogramgenre', VendorProgramGenreViewset)
router.register(r'supercommercials', SuperCommercialViewSet)
router.register(r'superprogram', SuperProgramViewSet)
router.register(r'superpromo', SuperPromoViewSet)
router.register(r'vendormastercomparisons', VendorMasterComparisonViewSet)
router.register(r'videopromos', VideoPromoViewSet, base_name='videopromos')
router.register(r'stats', StatViewSet, base_name='stats')
router.register(r'notifications', NotificationsViewSet, base_name='notifications')
router.register(r'songverification', SongVerificationViewSet, base_name='songverification')
router.register(r'assetversion', AssetVersionViewSet, base_name='assetversion')
router.register(r'collection', CollectionViewSet, base_name='collection')
router.register(r'assignworkflowinstancestep', AssignWorkFlowInstanceStepViewSet, base_name='assignworkflowinstancestep')
router.register(r'segment', SegmentViewSet, base_name='segment')
router.register(r'rushes', RushesViewSet, base_name='rushes')
router.register(r'contenttype', ContentTypeViewSet, base_name='contenttype')
router.register(r'generictag', GenericTagViewSet, base_name='generictag')
router.register(r'metadata_audio', MetadataAudioViewSet, base_name='metadataaudio')
router.register(r'manualtags', ManualTagViewSet, base_name='manualtags')
router.register(r'songasset', SongAssetViewSet, base_name='songasset')
router.register(r'batch', BatchViewSet, base_name='batch')
router.register(r'videoprocess_status', VideoProcessingStatusViewSet, base_name='videoprocessstatsus')
router.register(r'advancedsearch', AdvancedSearchViewSet, base_name='advancedsearch')
router.register(r'videoproxy_path', VideoProxyPathViewSet, base_name='videoproxypath')
router.register(r'sequence', SequenceViewSet, base_name='sequence')
router.register(r'manualtagqcstatus', ManualTagQCStatusViewSet, base_name='manualtagqcstatus')
router.register(r'season', SeasonViewSet, base_name='season')
router.register(r'clip', ClipViewSet, base_name='clip')
router.register(r'ticket', TicketViewSet, base_name='ticket')
router.register(r'workflow', WorkFlowViewSet, base_name='workflow')
router.register(r'workflowstep', WorkFlowStepViewSet, base_name='workflowstep')
router.register(r'workflowinstance', WorkFlowInstanceViewSet, base_name='workflowinstance')
router.register(r'workflowinstancestep', WorkFlowInstanceStepViewSet, base_name='workflowinstancestep')
router.register(r'workflowstage', WorkFlowStageViewSet, base_name='workflowstage')
router.register(r'workflowtransitionhistory', WorkFlowTransitionHistoryViewSet, base_name='workflowtransitionhistory')
router.register(r'roles', RoleViewSet)
router.register(r'workgroupmemberships', WorkGroupMembershipViewSet)
router.register(r'workflowcollectioninstance', WorkFlowCollectionInstanceViewSet, base_name='workflowcollectioninstance')
router.register(r'workflowcollectioninstancestep', WorkFlowCollectionInstanceStepViewSet, base_name='workflowcollectioninstancestep')
router.register(r'assignworkflowcollectioninstancestep', AssignWorkFlowCollectionInstanceStepViewSet, base_name='assignworkflowcollectioninstancestep')
router.register(r'publication', PublicationViewSet, base_name='publication')
router.register(r'commercialasset', CommercialAssetViewSet, base_name='commercialasset')
router.register(r'demo', DemoViewSet, base_name='demo')
router.register(r'auth_otp', AuthOTPViewSet, base_name="auth-otp")
router.register(r'feedback', FeedbackViewSet, base_name="feedback")
router.register(r'create_endpoints', CreateEndpointViewset, base_name="create-endpoints")
router.register(r'delete_endpoints', DeleteEndpointViewset, base_name="delete-endpoints")




# router.register(r'translation_job_assigned', SubtitleTranslationJobAssignedViewSet, base_name="translation-assigned")
# users nested router
user_router = routers.NestedSimpleRouter(router, r'users', lookup='users')
user_router.register(r'permissions', UserPermissionsViewSet, base_name='users-permissions')

# workgroup nested router
workgroup_router = routers.NestedSimpleRouter(router, r'workgroups', lookup='workgroups')
workgroup_router.register(r'videos', WorkGroupVideosViewSet, base_name='workgroups-videos')
workgroup_router.register(r'members', WorkGroupMembersViewSet, base_name='workgroups-members')
workgroup_router.register(r'permissions', WorkGroupPermissionsViewSet, base_name='workgroups-permissions')
workgroup_router.register(r'tagging_jobs', WorkGroupTaggingJobsViewSet, base_name='workgroups-tagging-jobs')
# favicon
favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    url(r'^api/v1/library/delete_multiple/', library_delete, name='library_delete'),
    url(r'^api/v1/library/', library, name='library'),
    url(r'^api/v1/library_search/', librarysearch, name='library_search'),
    url(r'^api/v1/generate_report/', generate_report, name='generate_report'),
    url(r'^api/v1/forgot_password/', forgot_password, name='forgot_password'),
    url(r'api/v1/reset_password', UpdatePasswordViewSet.as_view(), name="reset_password"),
    url(r'api/v1/update_password', ProfilePasswordViewSet.as_view(), name="update_password"),
    url(r'^api/v1/set_thumbnail', SetThumbnail.as_view(), name='set_thumbnail'),
    url(r'^aws_uploadid/', aws_uploadid, name='awsuploadid'),
    url(r'^aws_presigned_url/', aws_presigned_url, name='aws_presigned_url'),
    url(r'^aws_complete/', aws_complete, name='aws_complete'),
    url(r'^nested_admin/', include('nested_admin.urls')),
    # url(r'^admin/', include(admin_site.urls)),
    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^admin/', include(admin.site.urls)),              # admin urls
    url(r'^auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    url(r'^auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # url(r'^api/v1/', include('authentication.urls')),       # authentication urls for WebAPI
    url(r'^api/v1/', include(router.urls)),                 # app urls from router
    url(r'^api/v1/', include(user_router.urls)),            # user nested router
    url(r'^api/v1/', include(workgroup_router.urls)),       # workgroup nested router
    url('^inbox/notifications/', include(notifications.urls, namespace='notifications')),
    
    url(r'^favicon\.ico$', favicon_view),                   # TODO get a favicon designed
    url(r'^_ah/health/', HealthCheck.as_view()),
    # url(r'^docs/', include_docs_urls(title=API_TITLE, description=API_DESCRIPTION)),
    url(r'^docs/', include('rest_framework_docs.urls')),
    # the 'api-root' from django rest-frameworks default router
    url(r'^$', RedirectView.as_view(url=reverse_lazy('api-root'), permanent=False)),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


