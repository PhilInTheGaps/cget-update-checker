import sys
import os
import shlex
import collections
import semver
import re
import requests
import functools

BASEVERSION = re.compile(
    r"[a-zA-Z_\-]*(?P<major>0|[1-9]\d*)([\.\-_](?P<minor>\d*)([\.\-_](?P<patch>0|[1-9]\d*))?)?(\-?(?P<prerelease>[a-zA-Z]+\.?\d*))?(\+(?P<build>[a-zA-Z\.0-9]+))?",
    re.VERBOSE,
)

Version = collections.namedtuple(
    "Version", ["tag", "sem_version"])

Package = collections.namedtuple(
    "Package", ["source", "version", "newest", "is_supported"])


def get_semver(version):
    if semver.VersionInfo.isvalid(version):
        return version

    match = BASEVERSION.search(version)
    if not match:
        raise ValueError()

    ver = {
        "major": 0 if match["major"] is None else match["major"],
        "minor": 0 if match["minor"] is None else match["minor"],
        "patch": 0 if match["patch"] is None else match["patch"]
    }

    if match["prerelease"] is not None:
        ver["prerelease"] = match["prerelease"]

    if match["build"] is not None:
        ver["build"] = match["build"]

    return str(semver.VersionInfo(**ver))


def print_packages(supported: list[Package], unsupported: list[Package]):
    for p in supported:
        if p.version != p.newest:
            print(p.source + ": \033[91m{}\033[00m".format(p.version) + " -> \033[92m{}\033[00m".format(p.newest))
        else:
            print(p.source + ": \033[92m{}\033[00m".format(p.version))

    print("\nThe following packages could not be checked automatically:")

    for p in unsupported:
        print(p.source + ": " + p.version)


def cmp_versions(v1: Version, v2: Version) -> bool:
    try:
        return semver.compare(v1.sem_version, v2.sem_version)
    except ValueError:
        print("Error while comparing " + v1 + " and " + v2)
        return False


def get_newest_version(versions: list[Version]) -> Version:
    version_list = []

    for v in versions:
        try:
            sv = get_semver(v)
            version_list.append(Version(v, sv))
        except ValueError:
            continue

    version_list.sort(key=functools.cmp_to_key(cmp_versions), reverse=True)
    return version_list[0]


def find_newest_version(source: str) -> Version:
    url = f"https://api.github.com/repos/{source}/tags?per_page=100"
    data = requests.get(url)

    versions = []

    for tag in data.json():
        versions.append(tag["name"])

    return get_newest_version(versions)


def parse_tokens(tokens: list[str]) -> Package:
    sourceSplit = tokens[0].split("@")
    if len(sourceSplit) > 1:
        source = sourceSplit[0]
        version = sourceSplit[1]

        try:
            get_semver(version)
        except ValueError:
            return Package(tokens[0], version, version, False)

        newest = find_newest_version(source).tag

        return Package(sourceSplit[0], version, newest, True)

    return Package(tokens[0], "-", "-", False)


def load_file(file):
    if not os.path.exists(file):
        print("file not found: " + file)
        return

    with open(file) as f:
        supported = []
        unsupported = []

        for line in f.readlines():
            tokens = shlex.split(line, comments=True)
            if len(tokens) > 0:
                r = parse_tokens(tokens)
                if r.is_supported:
                    supported.append(r)
                else:
                    unsupported.append(r)

        print_packages(supported, unsupported)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No requirements file provided")
        exit(-1)

    load_file(sys.argv[1])
