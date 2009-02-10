# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf.urls.defaults import *
from django.conf import settings
import nbio.django.views
import frnda.views

HOST = 'host'
PATH = 'path'
APP_HOST = settings.HOSTS['app']
STATIC_HOST = settings.HOSTS['static']

urlpatterns = patterns('',
    (r'^pdf/$', frnda.views.pdf, {HOST: APP_HOST}),
    (r'^/?$', frnda.views.home, {HOST: APP_HOST}),
    (r'^home/?$', nbio.django.views.null, {HOST: APP_HOST, PATH: '/'}),
    (r'^.*', nbio.django.views.default, {HOST: APP_HOST}),
)
