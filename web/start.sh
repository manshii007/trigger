#!/bin/bash

clear

# migrate
python3 manage.py migrate

# jobtype
python3 manage.py loaddata jobs/fixtures/jobtype.json

# tags
python3 manage.py loaddata tags/fixtures/category.json tags/fixtures/tag.json

# library
python3 manage.py loaddata video/fixtures/videolibrary.json

# workgroup
python3 manage.py loaddata workgroups/fixtures/group.json workgroups/fixtures/workgroup.json workgroups/fixtures/user.json