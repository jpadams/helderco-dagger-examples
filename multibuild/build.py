"""
Create a multi-build pipeline for a Go application.

This example replicates the "Get Started with the Dagger Go SDK"
guide (in https://docs.dagger.io/sdk/go/959738/get-started) to
demonstrate how the common API behind Dagger SDKs make them
easily portable between each other.

This can be useful to adapt or take ideas from a use case that's
written in another language.
"""
import sys

import anyio
import dagger
import graphql


async def build():
    print("Building with Dagger")

    # define build matrix
    oses = ["linux", "darwin"]
    arches = ["amd64", "arm64"]

    # initialize dagger client
    cfg = dagger.Config(log_output=sys.stderr)
    async with dagger.Connection(cfg) as client:

        # get reference to the local project
        src_id = await client.host().directory(".").id()

        # create empty directory to put build outputs
        outputs = client.directory()

        golang = (
            # get `golang` image
            client.container().from_(f"golang:latest")

            # mount source code into `golang` image
            .with_mounted_directory("/src", src_id)
            .with_workdir("/src")
        )

        for goos in oses:
            for goarch in arches:
                # create a directory for each os and arch
                path = f"build/{goos}/{goarch}/"

                build = (
                    golang
                    # set GOARCH and GOOS in the build environment
                    .with_env_variable("GOOS", goos)
                    .with_env_variable("GOARCH", goarch)

                    # build application
                    .exec(["go", "build", "-o", path])
                )

                # get reference to build output directory in container
                dir_id = await build.directory(path).id()
                outputs = outputs.with_directory(path, dir_id)

        # write build artifacts to host
        await outputs.export(".")


if __name__ == "__main__":
    try:
        anyio.run(build)
    except graphql.GraphQLError as e:
        print(e.message)
        sys.exit(1)
