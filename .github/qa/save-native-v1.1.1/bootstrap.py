"""Isolated exact-tag native Windows QA; no settings or permission changes."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request

parser=argparse.ArgumentParser()
parser.add_argument('--bundle',required=True)
parser.add_argument('--root',required=True)
args=parser.parse_args()
root=Path(args.root)
assert root.is_absolute() and '..' not in root.parts and root==root.resolve()
assert not root.exists() and all(not p.is_symlink() for p in root.parents)
root.mkdir()
evidence=root/'evidence';evidence.mkdir()
def save(name,data):
    (evidence/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
try:
    assert platform.system()=='Windows' and sys.version_info>=(3,10)
    raw=Path(args.bundle).read_bytes()
    committed=subprocess.check_output(['git','show','HEAD:.github/qa/save-native-v1.1.1/transfer.json'])
    save('TRANSFER-BYTES.json',{'expected_sha256':'e7a56dca287089b45af13477f8b61e85d5e42db18a95c894aebcfef1250bfeb2','working_tree_sha256':hashlib.sha256(raw).hexdigest(),'working_tree_bytes':len(raw),'working_tree_lf':raw.count(b'\n'),'working_tree_crlf':raw.count(b'\r\n'),'committed_sha256':hashlib.sha256(committed).hexdigest(),'committed_bytes':len(committed),'committed_lf':committed.count(b'\n'),'committed_crlf':committed.count(b'\r\n'),'working_tree_bootstrap_sha256':digest(Path(__file__))})
    assert hashlib.sha256(raw).hexdigest()=='e7a56dca287089b45af13477f8b61e85d5e42db18a95c894aebcfef1250bfeb2'
    assert hashlib.sha256(committed).hexdigest()=='e7a56dca287089b45af13477f8b61e85d5e42db18a95c894aebcfef1250bfeb2'
    bundle=json.loads(raw)
    assert bundle['schema_version']==1 and bundle['slug']=='save-file-backup-recipe-generator'
    assert bundle['version']=='v1.1.1' and bundle['commit']=='47dea37455b93047330350637fe63780d99f2e65'
    assert bundle['tag_object']=='f05e77288d5fa4622d376cd50454d747071481b2' and bundle['tag_run']==39485085532
    required_inputs={'save_native_runner.py':'a7611b04c1fcc737643f57b1276701ff601cc317e55bde1a4a28101ea6fef115','save-native-public-CANDIDATE.json':'042d4fa3f0a0386d6a15ed55b440295ff5feec621009854dc73d20b6903b38b8','NATIVE-REQUIREMENTS.json':'274509f2538b94fb7a6f2e917f6692cf0ad298fb20f631abdfdf4d497b0e223f','NATIVE-CRITERIA-REVIEW.json':'90d6cb7768cd1a41ef1c468d6dd4c783145da3879cf34eeaeb66697581b03c2b'}
    required_artifacts={'save_file_backup_recipe_generator-1.1.1-py3-none-any.whl':'c41b2a23a15e0269a707d7dbc3c78cff6ddec4656dfc262ef12e94d1b191d7f3','save_file_backup_recipe_generator-1.1.1.tar.gz':'0e0a8fa9ab43014ae7bad4a0cfa71ddf5f84837e79d4d8e3185ee0e4f2175de2','SHA256SUMS':'2d36b2fce11a9229271304abacf68149a543b7b299e779b81363c88acd7f0a79'}
    assert set(bundle['files'])==set(required_inputs)|set(required_artifacts)
    inputs=root/'inputs';inputs.mkdir();artifacts=root/'artifacts';artifacts.mkdir();source=root/'source';source.mkdir()
    for name,expected in {**required_inputs,**required_artifacts}.items():
        row=bundle['files'][name];assert row['sha256']==expected and row['kind']==('input' if name in required_inputs else 'artifact')
        data=base64.b64decode(row['base64'],validate=True);assert hashlib.sha256(data).hexdigest()==expected
        (inputs/name if name in required_inputs else artifacts/name).write_bytes(data)
    candidate=json.loads((inputs/'save-native-public-CANDIDATE.json').read_text())
    assert set(candidate)==set(['slug', 'version', 'commit', 'tag_object', 'tag_run', 'tag_artifact_hashes', 'source_files', 'source_files_sha256'])
    assert bundle['candidate_projection']=={'variant': 'public-routing-projection-v1', 'original_sha256': 'b833781bfa605c2fd1c79c8ee003af907bf3dd1509b0501cb8a87f6e62e86b3e', 'actual_projection_sha256': '042d4fa3f0a0386d6a15ed55b440295ff5feec621009854dc73d20b6903b38b8', 'fields': ['slug', 'version', 'commit', 'tag_object', 'tag_run', 'tag_artifact_hashes', 'source_files', 'source_files_sha256'], 'values_equal_to_frozen_original': True}
    assert candidate['commit']==bundle['commit'] and candidate['tag_object']==bundle['tag_object'] and candidate['tag_run']==bundle['tag_run']
    assert candidate['tag_artifact_hashes']==required_artifacts
    assert candidate['source_files_sha256']==bundle['source_manifest_sha256']=='fccf4e4e9bd0de279a4cdb222c5e42a139008f38f58e2d11d629b95a86042b92'
    repo='loganpendragonmultiverse/save-file-backup-recipe-generator'
    for name,expected in candidate['source_files'].items():
        relative=Path(name);assert not relative.is_absolute() and '..' not in relative.parts
        request=urllib.request.Request('https://raw.githubusercontent.com/'+repo+'/'+bundle['commit']+'/'+name,headers={'User-Agent':'Forge-exact-tag-native-QA'})
        with urllib.request.urlopen(request,timeout=60) as response:data=response.read(1048577)
        assert len(data)<=1048576 and hashlib.sha256(data).hexdigest()==expected,name
        target=source/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    preflight=root/'preflight';preflight.mkdir();referent=preflight/'referent';referent.mkdir();(referent/'slot').write_bytes(b'synthetic save')
    filelink=preflight/'file-link';filelink.symlink_to(referent/'slot');assert filelink.is_symlink() and filelink.read_bytes()==b'synthetic save'
    dirlink=preflight/'directory-link';dirlink.symlink_to(referent,target_is_directory=True);assert dirlink.is_symlink() and (dirlink/'slot').read_bytes()==b'synthetic save'
    dangling=preflight/'dangling-link';dangling.symlink_to(preflight/'missing',target_is_directory=True);assert dangling.is_symlink() and not dangling.exists()
    pwsh=shutil.which('pwsh');assert pwsh
    junction=preflight/'junction'
    quote=lambda p:"'"+str(p).replace("'","''")+"'"
    command='New-Item -ItemType Junction -Path '+quote(junction)+' -Target '+quote(referent)+' | Out-Null'
    result=subprocess.run([pwsh,'-NoProfile','-Command',command],capture_output=True,text=True,check=True)
    assert getattr(junction.lstat(),'st_file_attributes',0)&0x400
    assert (junction/'slot').read_bytes()==b'synthetic save' and (referent/'slot').read_bytes()==b'synthetic save'
    save('PREFLIGHT.json',{'passed':True,'platform':platform.platform(),'python':sys.version,'file_symlink':True,'directory_symlink':True,'dangling_symlink':True,'junction':True,'security_settings_changed':False,'bundle_sha256':hashlib.sha256(raw).hexdigest(),'input_sha256s':required_inputs,'artifact_sha256s':required_artifacts})
    identity={k:os.environ.get(k) for k in ('GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_SHA','GITHUB_REF','GITHUB_REPOSITORY','RUNNER_OS','RUNNER_NAME','RUNNER_ARCH','ImageOS','ImageVersion')}
    save('HOSTED-RUN.json',{'execution_environment':identity,'bundle_sha256':hashlib.sha256(raw).hexdigest(),'artifact_origin':bundle['artifact_origin'],'exact_commit':bundle['commit'],'tag_object':bundle['tag_object'],'tag_run':bundle['tag_run'],'input_sha256s':required_inputs,'artifact_sha256s':required_artifacts,'runner_sha256':required_inputs['save_native_runner.py'],'source_manifest_sha256':candidate['source_files_sha256'],'candidate_projection':bundle['candidate_projection']})
    env=dict(os.environ);env.pop('PYTHONPATH',None)
    command=[sys.executable,'-B',str(inputs/'save_native_runner.py'),'--candidate',str(inputs/'save-native-public-CANDIDATE.json'),'--source',str(source),'--artifacts',str(artifacts),'--requirements',str(inputs/'NATIVE-REQUIREMENTS.json'),'--criteria-review',str(inputs/'NATIVE-CRITERIA-REVIEW.json'),'--output',str(root/'outputs')]
    with (evidence/'runner.log').open('w',encoding='utf-8') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=False,env=env)
    outputs=root/'outputs'
    if outputs.exists():
        for kind in ('wheel','sdist'):
            current=outputs/kind
            if current.is_dir():
                destination=evidence/kind;destination.mkdir()
                for file in current.iterdir():
                    if file.is_file() and file.suffix in ('.log','.xml'):shutil.copyfile(file,destination/file.name)
        if (outputs/'RESULT.json').is_file():shutil.copyfile(outputs/'RESULT.json',evidence/'RESULT.json')
    for name,expected in required_inputs.items():assert digest(inputs/name)==expected
    for name,expected in required_artifacts.items():assert digest(artifacts/name)==expected
    for name,expected in candidate['source_files'].items():assert digest(source/name)==expected
    assert result.returncode==0,'Exact installed native runner failed; inspect runner and per-artifact logs'
    outcome=json.loads((evidence/'RESULT.json').read_text());assert outcome['passed'] is True and outcome['platform']=='Windows' and outcome['native_runtime'] is True
    assert outcome['candidate_sha256']==required_inputs['save-native-public-CANDIDATE.json'] and outcome['runner_sha256']==required_inputs['save_native_runner.py']
    save('EVIDENCE-HASHES.json',{str(p.relative_to(evidence)):digest(p) for p in evidence.rglob('*') if p.is_file()})
    print('Exact-tag installed native Windows acceptance completed; independent review remains required')
except BaseException as exc:
    save('FAILURE.json',{'passed':False,'exception':type(exc).__name__,'message':str(exc),'platform':platform.platform()})
    raise
