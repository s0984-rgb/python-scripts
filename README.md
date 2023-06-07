# Python Scripts
This repo contains useful scripts for system administration tasks.

The goal of these scripts is to be run standalone or inside a container as an automated process.

## [Archivist](./archivist/)
This is a project that allows backing up a specified directory into a compress tarfile and pushed onto S3 object storage, while recording all objects stored in a tarfile into a statefile. It is also capable of monitoring a directory and restoring missing files.

It is compatible with AWS and self-hosted TLS enabled object storage.

It is intended to be run as a side car to a running process which does not have a method of clustering, by leveraging S3 object storage to syncronize storage across all running nodes.

## [Gardener](./gardener/)

This is a script that allows you to monitor a directory and delete files that have modification time greater that specified.

it is designed to be run as a scheduled task, or cronjob or inside a container.
