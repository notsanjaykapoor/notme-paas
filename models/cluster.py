import datetime
import typing

import sqlalchemy
import sqlmodel


CLOUD_DEFAULT = "hetzner"

SERVER_IMAGE_DEFAULT = "ubuntu-24.04"
SERVER_LOC_DEFAULT = "ash"
SERVER_TYPE_DEFAULT = "cpx11"

STATE_ACTIVE = "active"
STATE_DELETED = "deleted"


class Cluster(sqlmodel.SQLModel, table=True):
    __tablename__ = "clusters"
    __table_args__ = (sqlalchemy.UniqueConstraint("name", name="_name"),)

    id: typing.Optional[int] = sqlmodel.Field(default=None, primary_key=True)

    created_at: datetime.datetime = sqlmodel.Field(
        sa_column=sqlalchemy.Column(sqlalchemy.DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
    )
    data: dict = sqlmodel.Field(
        default_factory=dict, sa_column=sqlmodel.Column(sqlmodel.JSON)
    )
    name: str = sqlmodel.Field(index=True, nullable=False)
    size_ask: int = sqlmodel.Field(index=True, nullable=False)
    size_has: int = sqlmodel.Field(index=True, nullable=False)
    state: str = sqlmodel.Field(index=True, nullable=False)

    @property
    def cloud(self) -> str:
        return self.data.get("cloud") or ""

    @property
    def server_image(self) -> str:
        return self.data.get("server_image") or ""

    @property
    def server_location(self) -> str:
        return self.data.get("server_location") or ""

    @property
    def server_type(self) -> str:
        return self.data.get("server_type") or ""

    @property
    def services(self) -> str:
        return self.data.get("services") or ""