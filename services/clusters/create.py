import re

import sqlmodel

import models


def create(db_session: sqlmodel.Session, name: str, services: str, data: dict={}) -> models.Cluster:
    if not re.match("^[a-z0-9-]+$", name):
        raise ValueError("name invalid")

    data_merged = data | {
        "cloud": models.cluster.CLOUD_DEFAULT,
        "server_image": models.cluster.SERVER_IMAGE_DEFAULT,
        "server_location": models.cluster.SERVER_LOC_DEFAULT,
        "server_type": models.cluster.SERVER_TYPE_DEFAULT,
        "services": services,
    }

    cluster = models.Cluster(
        data=data_merged,
        name=name,
        size_ask=0,
        size_has=0,
        state=models.cluster.STATE_RUNNING,
    )

    db_session.add(cluster)
    db_session.commit()

    return cluster
