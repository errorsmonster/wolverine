import motor.motor_asyncio
from info import DATABASE_URI

DATABASE_NAME = 'group_api'

class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.grp = self.db.groups

    async def add_group(self, group_id):
        group_data = {
            'id': group_id,
            'sapi': ''
        }
        await self.grp.insert_one(group_data)

    async def remove_group(self, group_id):
        await self.grp.delete_one({'id': group_id})

    async def is_group_connected(self, group_id):
        group = await self.grp.find_one({'id': group_id})
        return group is not None

    async def is_api_available(self, group_id):
        group = await self.grp.find_one({'id': group_id, 'sapi': {'$ne': ''}})
        return group is not None

    async def get_api_from_chat(self, group_id):
        group = await self.grp.find_one({'id': group_id})
        return group.get('sapi', '')

    async def update_api_for_group(self, group_id, sapi):
        await self.grp.update_one({'id': group_id}, {'$set': {'sapi': sapi}})


gdb = Database(DATABASE_URI, DATABASE_NAME)
