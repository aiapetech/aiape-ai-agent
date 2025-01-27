from sqladmin import Admin, ModelView
from models.postgres_models import *

from models.postgres_models import *


class ChannelAdmin(ModelView, model=Channels):
    column_list = [Channels.id, Channels.name, Channels.description]
    can_edit = True
    can_create = True


class ProfileAdmin(ModelView, model=Profiles):
    column_list = [Profiles.id, Profiles.name,Profiles.link, "channel_name", Profiles.keywords]
    can_edit = True
    can_create = True

class PostAdmin(ModelView, model=Posts):
    column_list = [Posts.id,"author_name", Posts.link, Posts.title, Posts.posted_at, Posts.status]
    column_details_list = ["author_name", Posts.id, Posts.link, Posts.title, Posts.posted_at, Posts.status, Posts.content]
    column_formatters_detail = {
        Posts.author: lambda m, p:Posts.author.name
    }
    can_edit = True
    can_create = True






class SQLModelAdmin(Admin):
    def __init__(self, app, engine):
        super().__init__(app, engine)
        self.add_view(ChannelAdmin)
        self.add_view(ProfileAdmin)
        self.add_view(PostAdmin)
        