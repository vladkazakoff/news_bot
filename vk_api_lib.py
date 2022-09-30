import vk_api
from config import vk_login, vk_password


class VkApiLib:
    def __init__(self):
        vk_session = vk_api.VkApi(vk_login, vk_password)
        vk_session.auth(token_only=True)
        self.vk = vk_session.get_api()

    def get_wall_posts(self, count, group_id):
        return self.vk.wall.get(count=count, owner_id=group_id, filter='owner')

    def get_group_info(self, group_id):
        return self.vk.groups.getById(group_id=group_id, fields='members_count')
