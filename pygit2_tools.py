import pygit2
import os
from getpass import getpass

# https://www.pygit2.org/recipes/git-clone-ssh.html
class RemoteCallbacks(pygit2.RemoteCallbacks):
    def credentials(self, url, username_from_url, allowed_types):
        if allowed_types & pygit2.credentials.GIT_CREDENTIAL_USERNAME:
            return pygit2.Username('git')
        elif allowed_types & pygit2.credentials.GIT_CREDENTIAL_SSH_KEY:
            passphrase = getpass('passphrase: ')
            return pygit2.Keypair('git', os.path.expanduser('~/.ssh/id_rsa.pub'), os.path.expanduser('~/.ssh/id_rsa'), passphrase)
        else:
            return None
        

# https://github.com/MichaelBoselowitz/pygit2-examples
def pull(repo, remote_name='origin'):
    for remote in repo.remotes:
        if remote.name == remote_name:
            remote.fetch(callbacks=RemoteCallbacks())
            remote_master_id = repo.lookup_reference('refs/remotes/origin/master').target
            merge_result, _ = repo.merge_analysis(remote_master_id)
            # Up to date, do nothing
            if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                return
            # We can just fastforward
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                repo.checkout_tree(repo.get(remote_master_id))
                master_ref = repo.lookup_reference('refs/heads/master')
                master_ref.set_target(remote_master_id)
                repo.head.set_target(remote_master_id)
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
                repo.merge(remote_master_id)
                print(repo.index.conflicts)

                assert repo.index.conflicts is None, 'Conflicts, ahhhh!'
                user = repo.default_signature
                tree = repo.index.write_tree()
                commit = repo.create_commit('HEAD',
                                            user,
                                            user,
                                            'Merge!',
                                            tree,
                                            [repo.head.target, remote_master_id])
                repo.state_cleanup()
            else:
                raise AssertionError('Unknown merge analysis result')