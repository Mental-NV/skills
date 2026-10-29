#!/usr/bin/env python3
"""Read GitHub metadata/settings and emit exact default Azure trust; never mutate."""
import argparse
import json
import re
import subprocess
import sys


class DiscoveryError(ValueError):
    pass


def github_json(repository, suffix=''):
    result = subprocess.run(['gh', 'api', '--hostname', 'github.com', '--method', 'GET',
                             f'repos/{repository}{suffix}'],
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise DiscoveryError('GitHub metadata/settings unreadable; verify gh authentication and repository access. No mutation attempted.')
    try:
        value = json.loads(result.stdout)
    except ValueError as error:
        raise DiscoveryError('GitHub returned invalid JSON; discovery stopped.') from error
    if not isinstance(value, dict):
        raise DiscoveryError('GitHub returned unexpected metadata; discovery stopped.')
    return value


def discover(repository, metadata, settings, context, value=None, observed=None,
             audience='api://AzureADTokenExchange'):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise DiscoveryError('Repository must be OWNER/REPO on public GitHub.')
    if metadata.get('full_name') != repository:
        raise DiscoveryError('Metadata differs from the requested canonical repository; inspect rename/redirect/case.')
    if settings.get('use_default') is not True:
        raise DiscoveryError('Custom/inherited template: inspect effective claims and actual sanitized assertion; this helper does not guess custom subjects.')
    owner = metadata.get('owner')
    if not isinstance(owner, dict) or owner.get('login') != repository.split('/')[0]:
        raise DiscoveryError('Repository owner metadata does not match.')
    owner_id, repo_id = owner.get('id'), metadata.get('id')
    if any(type(identifier) is not int or identifier <= 0 for identifier in (owner_id, repo_id)):
        raise DiscoveryError('Immutable owner/repository IDs missing or invalid.')
    mode = settings.get('use_immutable_subject')
    if mode is True:
        prefix = f"repo:{owner['login']}@{owner_id}/{repository.split('/')[1]}@{repo_id}"
    elif mode is False:
        prefix = 'repo:' + repository
    else:
        raise DiscoveryError('Unknown subject mode; inspect settings/actual assertion instead of assuming legacy format.')
    reported = settings.get('sub_claim_prefix')
    if reported is not None and reported != prefix:
        raise DiscoveryError('Reported prefix disagrees with repository IDs or subject mode.')
    if context not in ('environment', 'branch', 'tag', 'pull_request'):
        raise DiscoveryError('Unsupported job context.')
    if context == 'pull_request':
        suffix = 'pull_request'
    else:
        if not isinstance(value, str) or not value or any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise DiscoveryError('Context must be nonempty and contain no control characters.')
        if context in ('branch', 'tag') and value.startswith('refs/'):
            raise DiscoveryError('Supply a branch/tag name, not a refs/ path.')
        encoded = value.replace(':', '%3A')
        suffix = 'environment:' + encoded if context == 'environment' else f"ref:refs/{'heads' if context == 'branch' else 'tags'}/{encoded}"
    subject = prefix + ':' + suffix
    if observed is not None and observed != subject:
        raise DiscoveryError('Observed subject differs; inspect job environment/event and effective template. No mutation attempted.')
    if not audience or any(char.isspace() for char in audience):
        raise DiscoveryError('Audience must be a nonempty exact configured value without whitespace.')
    return {'repository': repository, 'ownerId': owner_id, 'repositoryId': repo_id,
            'mode': 'immutable' if mode else 'legacy', 'context': context,
            'issuer': 'https://token.actions.githubusercontent.com',
            'subject': subject, 'audiences': [audience],
            'observedSubjectMatches': True if observed is not None else None,
            'mutations': False, 'actionsExchangeVerified': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True, help='Canonical public GitHub OWNER/REPO.')
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument('--environment')
    selector.add_argument('--branch')
    selector.add_argument('--tag')
    selector.add_argument('--pull-request', action='store_true')
    parser.add_argument('--observed-subject', help='Sanitized sub claim only, never a JWT/token.')
    parser.add_argument('--audience', default='api://AzureADTokenExchange')
    args = parser.parse_args(argv)
    try:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repository):
            raise DiscoveryError('Repository must be OWNER/REPO on public GitHub.')
        metadata = github_json(args.repository)
        settings = github_json(args.repository, '/actions/oidc/customization/sub')
        context = next(name for name in ('environment', 'branch', 'tag', 'pull_request')
                       if getattr(args, name) is not None and getattr(args, name) is not False)
        result = discover(args.repository, metadata, settings, context, getattr(args, context),
                          args.observed_subject, args.audience)
        print(json.dumps(result, indent=2))
    except (DiscoveryError, OSError, subprocess.TimeoutExpired) as error:
        message = str(error) if isinstance(error, DiscoveryError) else 'GitHub CLI unavailable or timed out; no mutation attempted.'
        print('OIDC discovery stopped: ' + message, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
