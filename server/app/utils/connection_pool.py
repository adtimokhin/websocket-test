from collections import OrderedDict
from typing import Dict, Optional

# Do improvements in O-time in this case come with the space-complexity?
#
# When agents search for available 'user rooms' to join, they essentially
# are looking through all connections to see which one they can help.
# That leads to O(n), where n is a number of all connections.
# This can be easily be decreased to O(m), where m is a number of user connections
# with n > m. But that does not solve the complexity and does little optimization.
#
# Is there a way to introduce some sorting for agents to locate the user connections
# they can help faster? Idea - use tenant_id for such identification!
#
# Essentially, agents and users can only talk if their tenant ids match.
# Using hashmaps we can make the lookup time for the user-pool where a help
# might be needed (not the same as 'user-rooms'!) to O(1). This is good.
#
# Then in the pool of tenant-related users we need a way to find those users
# that await connection with an agent.
# Users can be practically in 3 states:
# 1) Talking to AI
# 2) Waiting for agent
# 3) Talking to agent
# Essentially, the question then boils down to sorting within the hashmap array
# of values that is mapped by a hasmap key (i.e. tenant_id).
# 
# Additional issue: we are storing in memory all connections, users and agents
# thus, we need to not only sort for the waiting for agent connections, but
# also for USER connections.
#
# We are concerned about being able to do the following:
# search for tenant_id -> search for USER connections -> search for 'Waiting for agent' connections
#
# Honestly, apart from this operation, we will not be doing anything else in terms of searching.
# We can simply add to the hashmap only those connections that will match the following:
# 1) They are user connections
# 2) They are 'Waiting for agent' connections
# Then for the lookup we will simply return the first item from the list matched by the tenant_id
# Complexity: O(1)
#
# Adding new awaiting connections:
# Simple - when user switches mode, they will be added to the datastructure
# Time complexity of insertion: O(1). If too many cleints use the same tenant this can grow to O(n)
#
# Removing the connections:
# Use tenant_id to find the bucket (O(1)), iterate through the whole array to find the connection. O(k)
# Time complexity: O(k)
#
# Deletion time can be improved by introducing some sort of sorting into these arrays. Maybe based on websocket ids, or similar.
#
# Time complexity at this stage:
# 1) Lookup of any available user -> O(1)
# 2) Adding new user -> O(1)
# 3) Removing specific user -> O(n)
#
# Can we improve this?
#
# To be able to remove the connection from the list of pending connections,
# We need to allow optimized search within the inner datastructure.
#
# Idea: We can sort them based on some id field.
# Maybe use an AVL-tree for the connections?
# Insertion: O(log n)
# Deletion: O(log n)
# Full search: O(n) <-- But we will never do that
#
# For finding a node in the AVL-tree for agent to pick up new conversation,
# We will return the root of the tree. This will mean that the time complexity
# for finding a new connection for the agent will be of O(1) time complexity.
#
#
# This selection of the next user to help brings an issue with the fairness
# of who gets the help next. It makes sense to help in the order of incomming
# requests. That will mean that the IDs of these connections will be important.
# We should start answering the smallest ID request first.
# Finding this element has complexity of O(log n)
#
# This brings overall complexity of finding/inserting/deleting elements to
# O(log n)
#
# After some thinking, I decided to replace the AVL trees with simple ordered
# list. It will make it easier to track the order of the connections in O(1)
# time. And we can use the ordered dict for finding a particular connection in 
# a list, also in O(1) time.

class Connection:
    def __init__(self, conn_id: str, tenant_id: str, data:any):
        self.conn_id = conn_id
        self.tenant_id = tenant_id
        self.data = data

    def __repr__(self):
        return f"<Connection id={self.conn_id} tenant={self.tenant_id}>"

class WaitingPool:
    def __init__(self):
        self.pool: Dict[str, OrderedDict[str, Connection]] = {}

    def add_connection(self, conn: Connection):
        """Add a new user connection to the waiting pool."""
        if conn.tenant_id not in self.pool:
            self.pool[conn.tenant_id] = OrderedDict()
        self.pool[conn.tenant_id][conn.conn_id] = conn

    def remove_connection(self, tenant_id: str, conn_id: str) -> bool:
        """Remove a specific connection from the pool."""
        tenant_bucket = self.pool.get(tenant_id)
        if tenant_bucket and conn_id in tenant_bucket:
            del tenant_bucket[conn_id]
            if not tenant_bucket:
                del self.pool[tenant_id]  # Clean up empty bucket
            return True
        return False

    def get_next_connection(self, tenant_id: str) -> Optional[Connection]:
        """Get the oldest waiting user for a tenant."""
        tenant_bucket = self.pool.get(tenant_id)
        if tenant_bucket:
            return next(iter(tenant_bucket.values()))
        return None

    def __repr__(self):
        return f"<WaitingPool tenants={list(self.pool.keys())}>"
