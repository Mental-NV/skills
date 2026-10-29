import contextlib
import copy
import io
import json
import subprocess
import unittest
from unittest.mock import patch

import discover_subject as discovery


class SubjectDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.metadata = {'full_name': 'owner/repo', 'id': 456, 'owner': {'login': 'owner', 'id': 123}}
        self.settings = {'use_default': True, 'use_immutable_subject': True,
                         'sub_claim_prefix': 'repo:owner@123/repo@456'}

    def discover(self, context='environment', value='Staging', **kwargs):
        return discovery.discover('owner/repo', self.metadata, self.settings, context, value, **kwargs)

    def test_immutable_environment_exact_match_and_boundary(self):
        subject = 'repo:owner@123/repo@456:environment:Staging'
        result = self.discover(observed=subject)
        self.assertEqual(result['subject'], subject)
        self.assertEqual(result['issuer'], 'https://token.actions.githubusercontent.com')
        self.assertEqual(result['audiences'], ['api://AzureADTokenExchange'])
        self.assertTrue(result['observedSubjectMatches'])
        self.assertFalse(result['mutations'])
        self.assertFalse(result['actionsExchangeVerified'])

    def test_legacy_is_used_only_when_reported(self):
        self.settings.update(use_immutable_subject=False, sub_claim_prefix='repo:owner/repo')
        self.assertEqual(self.discover()['subject'], 'repo:owner/repo:environment:Staging')

    def test_contexts_colon_encoding_and_distinct_environments(self):
        for context, value, suffix in (
            ('environment', 'Production:V1', 'environment:Production%3AV1'),
            ('branch', 'feature/topic', 'ref:refs/heads/feature/topic'),
            ('tag', 'v1', 'ref:refs/tags/v1'),
            ('pull_request', None, 'pull_request')):
            with self.subTest(context=context):
                self.assertEqual(self.discover(context, value)['subject'], 'repo:owner@123/repo@456:' + suffix)
        self.assertNotEqual(self.discover(value='Production')['subject'], self.discover()['subject'])

    def test_missing_optional_prefix_uses_explicit_mode_and_verified_ids(self):
        del self.settings['sub_claim_prefix']
        self.assertEqual(self.discover()['subject'], 'repo:owner@123/repo@456:environment:Staging')

    def test_unknown_mode_custom_template_and_mismatched_prefix_stop(self):
        good = copy.deepcopy(self.settings)
        for change in ({'use_immutable_subject': None}, {'use_default': False},
                       {'sub_claim_prefix': 'repo:owner/repo'},
                       {'sub_claim_prefix': 'repo:owner@123/repo@999'}):
            with self.subTest(change=change):
                self.settings = dict(good, **change)
                with self.assertRaises(discovery.DiscoveryError):
                    self.discover()

    def test_metadata_redirect_and_invalid_ids_stop(self):
        good = copy.deepcopy(self.metadata)
        for change in ({'full_name': 'other/repo'}, {'id': 0}, {'id': True},
                       {'owner': {'login': 'other', 'id': 123}}):
            with self.subTest(change=change):
                self.metadata = dict(good, **change)
                with self.assertRaises(discovery.DiscoveryError):
                    self.discover()

    def test_observed_name_only_subject_is_not_silently_accepted(self):
        with self.assertRaises(discovery.DiscoveryError):
            self.discover(observed='repo:owner/repo:environment:Staging')

    def test_invalid_context_and_audience_stop(self):
        for context, value in (('environment', ''), ('environment', 'Staging\n'),
                               ('branch', 'refs/heads/main'), ('unknown', 'x')):
            with self.subTest(context=context, value=value), self.assertRaises(discovery.DiscoveryError):
                self.discover(context, value)
        with self.assertRaises(discovery.DiscoveryError):
            self.discover(audience='bad audience')

    def test_cli_uses_only_two_public_github_gets(self):
        replies = [subprocess.CompletedProcess([], 0, stdout=json.dumps(value), stderr='')
                   for value in (self.metadata, self.settings)]
        with patch.object(discovery.subprocess, 'run', side_effect=replies) as request, \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(discovery.main(['--repository', 'owner/repo', '--environment', 'Staging']), 0)
        self.assertEqual(json.loads(output.getvalue())['subject'], 'repo:owner@123/repo@456:environment:Staging')
        self.assertEqual([call.args[0] for call in request.call_args_list], [
            ['gh', 'api', '--hostname', 'github.com', '--method', 'GET', 'repos/owner/repo'],
            ['gh', 'api', '--hostname', 'github.com', '--method', 'GET', 'repos/owner/repo/actions/oidc/customization/sub']])

    def test_api_failure_does_not_echo_raw_diagnostics(self):
        reply = subprocess.CompletedProcess([], 1, stdout='', stderr='private-sentinel')
        with patch.object(discovery.subprocess, 'run', return_value=reply), \
             contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(discovery.main(['--repository', 'owner/repo', '--pull-request']), 1)
        self.assertNotIn('private-sentinel', error.getvalue())

    def test_multiple_context_flags_stop_before_network(self):
        with patch.object(discovery.subprocess, 'run') as request, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                discovery.main(['--repository', 'owner/repo', '--environment', 'Staging', '--branch', 'main'])
            request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
