#!/usr/bin/env python3
"""Real Secret Service synthetic-only probe; no secret values in receipts."""
import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

p = argparse.ArgumentParser()
p.add_argument('mode', choices=['cycle', 'read', 'absent'])
p.add_argument('--disposable-collection', action='store_true',
               help='create/delete only a new unaliased test collection; never unlock the login collection')
p.add_argument('--run-id', help=argparse.SUPPRESS)
p.add_argument('--item-path', help=argparse.SUPPRESS)
a = p.parse_args()
if a.disposable_collection and a.mode != 'cycle':
    p.error('--disposable-collection requires cycle')
if (a.run_id or a.item_path) and a.mode != 'read':
    p.error('internal item selection requires read')
if a.run_id and (len(a.run_id) != 32 or any(c not in '0123456789abcdef' for c in a.run_id)):
    p.error('invalid synthetic run identifier')
source_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
name = 'org.freedesktop.secrets'
if a.mode == 'absent':
    print(json.dumps({'case':'absent-service', 'owner_present': bool(bus.name_has_owner(name)), 'persistent_fallback_created':False, 'scope':'isolated D-Bus without activation services; no product registration tested', 'script_sha256':source_sha256}))
    raise SystemExit(bool(bus.name_has_owner(name)))
service = dbus.Interface(bus.get_object(name, '/org/freedesktop/secrets'), 'org.freedesktop.Secret.Service')
_, session = service.OpenSession('plain', dbus.String('', variant_level=1))
attrs = dbus.Dictionary({'campus-spike':'982-synthetic'}, signature='ss')
run_id = secrets.token_hex(16) if a.disposable_collection else a.run_id
if run_id:
    attrs['campus-spike-run'] = run_id
if a.mode == 'read':
    unlocked, locked = service.SearchItems(attrs)
    if not unlocked: raise SystemExit(2)
    selected = a.item_path or unlocked[0]
    if str(selected) not in [str(path) for path in unlocked]: raise SystemExit(2)
    secret = dbus.Interface(bus.get_object(name, selected), 'org.freedesktop.Secret.Item').GetSecret(session)
    matched = bytes(secret[2]) == b'campus982-synthetic-store-only'
    print(json.dumps({'same_uid_separate_process_read':matched, 'script_sha256':source_sha256}))
    raise SystemExit(0 if matched else 2)

def prompt(path, phase='awaiting-desktop-unlock-prompt'):
    if str(path) == '/': return {'needed':False, 'dismissed':False}
    loop = GLib.MainLoop()
    result = {'needed':True, 'timeout':True}
    timer_expired = False
    obj = dbus.Interface(bus.get_object(name, path), 'org.freedesktop.Secret.Prompt')
    def done(dismissed, value):
        result.update(timeout=False, dismissed=bool(dismissed))
        # CreateCollection/CreateItem return their object path through the prompt.
        # Never serialize arbitrary variant contents (or any secret value).
        if isinstance(value, dbus.ObjectPath):
            result['result_path'] = str(value)
        loop.quit()
    connection = obj.connect_to_signal('Completed', done)
    def expire():
        nonlocal timer_expired
        timer_expired = True
        loop.quit()
        return False
    timer = GLib.timeout_add_seconds(90, expire)
    print(json.dumps({'phase':phase}), flush=True)
    try:
        obj.Prompt('')
        if result['timeout']:
            loop.run()
        if result['timeout']:
            obj.Dismiss()
    finally:
        connection.remove()
        if not timer_expired:
            GLib.source_remove(timer)
    return result

def prompt_succeeded(result):
    return not result.get('dismissed', False) and not result.get('timeout', False)

service_props = dbus.Interface(bus.get_object(name, '/org/freedesktop/secrets'), 'org.freedesktop.DBus.Properties')
def collections():
    return {str(path) for path in service_props.Get('org.freedesktop.Secret.Service', 'Collections')}

aliases_before = {alias:str(service.ReadAlias(alias)) for alias in ('default', 'login')}
collections_before = collections()
owned_collection = None
if a.disposable_collection:
    label = 'Campus 982 disposable synthetic collection'
    collection, request = service.CreateCollection(dbus.Dictionary(
        {'org.freedesktop.Secret.Collection.Label':label}, signature='sv'), '')
    outcome = prompt(request, 'awaiting-desktop-create-disposable-collection-prompt')
    if str(collection) == '/':
        collection = outcome.get('result_path', '/')
    # Do not adopt or delete a returned preexisting collection or any known alias.
    if (not prompt_succeeded(outcome) or str(collection) == '/'
            or str(collection) in collections_before
            or str(collection) in aliases_before.values()
            or str(collection) not in collections()):
        print(json.dumps({'phase':'collection-create','pass':False,
                          'reason':'new unaliased collection identity not established',
                          'prompt':outcome,'script_sha256':source_sha256}), flush=True)
        raise SystemExit(1)
    check = dbus.Interface(bus.get_object(name,collection), 'org.freedesktop.DBus.Properties')
    if str(check.Get('org.freedesktop.Secret.Collection','Label')) != label:
        raise SystemExit('Unexpected collection label; refused to adopt or delete')
    owned_collection = str(collection)
    print(json.dumps({'phase':'collection-create','pass':True,'collection':owned_collection,
                      'alias':'','default_login_aliases_preserved':aliases_before ==
                          {alias:str(service.ReadAlias(alias)) for alias in ('default', 'login')},'prompt':outcome,
                      'scope':'new disposable collection; not PAM login keyring unlock evidence',
                      'script_sha256':source_sha256}),flush=True)
else:
    collection = aliases_before['default']
    if str(collection) == '/': collection = aliases_before['login']

def cycle():
    props = dbus.Interface(bus.get_object(name, collection), 'org.freedesktop.DBus.Properties')
    initial = bool(props.Get('org.freedesktop.Secret.Collection', 'Locked'))
    if initial:
        _, request = service.Unlock([collection]); outcome = prompt(request)
        if props.Get('org.freedesktop.Secret.Collection','Locked'): raise SystemExit('Collection remains locked; no synthetic item created')
    item, request = dbus.Interface(bus.get_object(name,collection),'org.freedesktop.Secret.Collection').CreateItem(
        dbus.Dictionary({'org.freedesktop.Secret.Item.Label':'Campus 982 disposable synthetic probe', 'org.freedesktop.Secret.Item.Attributes':attrs}, signature='sv'),
        dbus.Struct((session,dbus.Array([],signature='y'),dbus.Array(b'campus982-synthetic-store-only',signature='y'),'text/plain'), signature='oayays'), True)
    created_prompt = prompt(request)
    if str(item) == '/': item = created_prompt.get('result_path', '/')
    found_unlocked, found_locked = service.SearchItems(attrs)
    created = (str(item) != '/' and str(item) in [str(path) for path in list(found_unlocked) + list(found_locked)]
               and not created_prompt.get('dismissed', False) and not created_prompt.get('timeout', False))
    print(json.dumps({'phase':'store-unlocked', 'initial_locked':initial, 'item_created':created,
                      'script_sha256':source_sha256}),flush=True)
    if not created:
        raise SystemExit('Synthetic item creation unresolved; no creation pass claimed')
    child_argv = [sys.executable, __file__, 'read', '--item-path', str(item)]
    if run_id: child_argv += ['--run-id', run_id]
    child = subprocess.run(child_argv, env=dict(os.environ), close_fds=True,
                           capture_output=True, timeout=15)
    try:
        child_result = json.loads(child.stdout)
    except (ValueError, UnicodeDecodeError):
        child_result = {'same_uid_separate_process_read':False, 'read_result_unavailable':True}
    same_uid_read = child.returncode == 0 and child_result.get('same_uid_separate_process_read') is True
    print(json.dumps(child_result),flush=True)
    service.Lock([collection])
    locked = bool(props.Get('org.freedesktop.Secret.Collection', 'Locked'))
    try:
        dbus.Interface(bus.get_object(name,item),'org.freedesktop.Secret.Item').GetSecret(session)
        refused=False
    except dbus.DBusException as e:
        refused = e.get_dbus_name() == 'org.freedesktop.Secret.Error.IsLocked'
    print(json.dumps({'phase':'store-locked','locked':locked,'read_refused':refused}),flush=True)
    _, request = service.Unlock([collection])
    outcome = prompt(request)
    unlocked = not bool(props.Get('org.freedesktop.Secret.Collection','Locked')) and prompt_succeeded(outcome)
    print(json.dumps({'phase':'store-unlock','unlocked':unlocked,'prompt':outcome}),flush=True)
    deleted = False
    if unlocked:
        delete_request = dbus.Interface(bus.get_object(name,item),'org.freedesktop.Secret.Item').Delete()
        delete_prompt = prompt(delete_request)
        remaining_unlocked, remaining_locked = service.SearchItems(attrs)
        missing = str(item) not in [str(path) for path in list(remaining_unlocked) + list(remaining_locked)]
        deleted = missing and not delete_prompt.get('dismissed', False) and not delete_prompt.get('timeout', False)
        print(json.dumps({'phase':'cleanup','synthetic_item_deleted':deleted,
                          'item_missing_from_lookup':missing,'prompt':delete_prompt}),flush=True)
    else:
        print(json.dumps({'phase':'cleanup','synthetic_item_deleted':False,
                          'reason':'collection remains locked; cleanup still required'}),flush=True)
    return bool(created and same_uid_read and locked and refused and unlocked and deleted)

cycle_passed = False
collection_deleted = owned_collection is None
cleanup_error = None
try:
    cycle_passed = cycle()
except (Exception, SystemExit) as exc:
    # Do not print arbitrary exception payloads or secret service values.
    print(json.dumps({'phase':'cycle-failure','type':type(exc).__name__,
                      'pass':False,'script_sha256':source_sha256}),flush=True)
finally:
    if owned_collection is not None:
        try:
            # A path must remain both new and unaliased immediately before deletion.
            aliases_now = {alias:str(service.ReadAlias(alias)) for alias in ('default', 'login')}
            if owned_collection in collections_before or owned_collection in aliases_now.values():
                raise RuntimeError('Refused collection cleanup after ownership change')
            request = dbus.Interface(bus.get_object(name,owned_collection),
                                     'org.freedesktop.Secret.Collection').Delete()
            cleanup_prompt = prompt(request, 'awaiting-desktop-disposable-collection-delete-prompt')
            collection_deleted = prompt_succeeded(cleanup_prompt) and owned_collection not in collections()
            print(json.dumps({'phase':'collection-cleanup','collection':owned_collection,
                              'disposable_collection_deleted':collection_deleted,
                              'prompt':cleanup_prompt}),flush=True)
        except Exception as exc:
            cleanup_error = type(exc).__name__
            print(json.dumps({'phase':'collection-cleanup','disposable_collection_deleted':False,
                              'type':cleanup_error,'cleanup_required':owned_collection}),flush=True)
    aliases_after = {alias:str(service.ReadAlias(alias)) for alias in ('default', 'login')}
    defaults_preserved = aliases_before == aliases_after
    old_collections_preserved = collections_before.issubset(collections())
    passed = bool(cycle_passed and collection_deleted and not cleanup_error
                  and defaults_preserved and old_collections_preserved)
    print(json.dumps({'phase':'result','pass':passed,'script_sha256':source_sha256,
                      'collection_mode':'disposable-unaliased' if a.disposable_collection else 'existing-default',
                      'default_login_aliases_preserved':defaults_preserved,
                      'preexisting_collection_paths_preserved':old_collections_preserved,
                      'disposable_collection_deleted':collection_deleted if a.disposable_collection else None,
                      'pam_autounlock_proven':False}),flush=True)
raise SystemExit(0 if passed else 1)
