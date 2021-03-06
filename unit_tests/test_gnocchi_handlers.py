# Copyright 2016 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import print_function

import mock

import charms_openstack.test_utils as test_utils

import reactive.gnocchi_handlers as handlers


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        defaults = [
            'charm.installed',
            'shared-db.connected',
            'ha.connected',
            'identity-service.connected',
            'identity-service.available',
            'config.changed',
            'update-status',
            'charm.default-select-release']
        hook_set = {
            'when': {
                'render_config': (
                    'coordinator-memcached.available',
                    'shared-db.available',
                    'identity-service.available',
                ),
                'init_db': (
                    'config.rendered',
                ),
                'cluster_connected': (
                    'ha.connected',
                ),
                'provide_gnocchi_url': (
                    'metric-service.connected',
                    'config.rendered',
                    'db.synced',
                ),
            },
            'when_not': {
                'disable_services': (
                    'config.rendered',
                ),
                'cluster_connected': (
                    'ha.available',
                ),
                'init_db': (
                    'db.synced',
                ),
            },
        }
        # test that the hooks were registered via the
        # reactive.gnocchi_handlers
        self.registered_hooks_test_helper(handlers, hook_set, defaults)


class TestHandlers(test_utils.PatchHelper):

    def setUp(self):
        super(TestHandlers, self).setUp()
        self.gnocchi_charm = mock.MagicMock()
        self.gnocchi_charm.gnocchi_user = 'gnocchi'
        self.gnocchi_charm.gnocchi_group = 'gnocchi'
        self.patch_object(handlers.charm, 'provide_charm_instance',
                          new=mock.MagicMock())
        self.provide_charm_instance().__enter__.return_value = \
            self.gnocchi_charm
        self.provide_charm_instance().__exit__.return_value = None

    def test_render_stuff(self):
        handlers.render_config('arg1', 'arg2')
        self.gnocchi_charm.render_with_interfaces.assert_called_once_with(
            ('arg1', 'arg2')
        )
        self.gnocchi_charm.assess_status.assert_called_once_with()
        self.gnocchi_charm.enable_webserver_site.assert_called_once_with()

    def test_init_db(self):
        handlers.init_db()
        self.gnocchi_charm.db_sync.assert_called_once_with()

    @mock.patch.object(handlers.reactive.flags, 'is_flag_set')
    def test_provide_gnocchi_url(self, mock_is_flag_set):
        mock_is_flag_set.return_value = False
        mock_gnocchi = mock.MagicMock()
        self.gnocchi_charm.public_url = "http://gnocchi:8041"
        handlers.provide_gnocchi_url(mock_gnocchi)
        mock_gnocchi.set_gnocchi_url.assert_called_once_with(
            "http://gnocchi:8041"
        )

    @mock.patch.object(handlers.reactive.flags, 'is_flag_set')
    def test_provide_gnocchi_url_ha_connected(self, mock_is_flag_set):
        mock_is_flag_set.side_effect = [True, False]
        mock_gnocchi = mock.MagicMock()
        handlers.provide_gnocchi_url(mock_gnocchi)
        mock_gnocchi.set_gnocchi_url.assert_not_called()

    @mock.patch.object(handlers.reactive.flags, 'is_flag_set')
    def test_provide_gnocchi_url_ha_available(self, mock_is_flag_set):
        mock_is_flag_set.side_effect = [True, True]
        mock_gnocchi = mock.MagicMock()
        self.gnocchi_charm.public_url = "http://gnocchi:8041"
        handlers.provide_gnocchi_url(mock_gnocchi)
        mock_gnocchi.set_gnocchi_url.assert_called_once_with(
            "http://gnocchi:8041"
        )
