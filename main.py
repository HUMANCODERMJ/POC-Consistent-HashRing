import hashlib
import bisect

class ConsistentHashRing:
    def __init__(self, replicas=100):
        """
        replicas: Number of virtual nodes (toothpicks) per physical server.
        """
        self.replicas = replicas
        self.ring = []
        self.vnodes = {} # hash_value -> physical_server_name

    
    def _hash(self, key: str) -> int:

        md5_hex = hashlib.md5(key.encode('utf-8')).hexdigest()
        return int(md5_hex[:8], 16)

    def add_server(self, server: str) -> str:

        """Adds a physical server by creating multiple virtual nodes for it."""
        for i in range(self.replicas):
            vnode_key = f"{server}_vnode_{i}"
            vnode_hash = self._hash(vnode_key)
            
            # Place on the circle
            bisect.insort(self.ring, vnode_hash)
            self.vnodes[vnode_hash] = server

    def remove_server(self, server: str):

        """Removes a physical server and all its associated virtual nodes."""
        for i in range(self.replicas):
            vnode_key = f"{server}_vnode_{i}"
            vnode_hash = self._hash(vnode_key)
            
            idx = bisect.bisect_left(self.ring, vnode_hash)
            if idx < len(self.ring) and self.ring[idx] == vnode_hash:
                del self.ring[idx]
            if vnode_hash in self.vnodes:
                del self.vnodes[vnode_hash]

    def get_server(self, data_key: str) -> str:

        """Finds the closest server going clockwise from the data key's hash."""
        if not self.ring:
            return None

        key_hash = self._hash(data_key)
        
        # Binary search to find the next server clockwise
        idx = bisect.bisect_right(self.ring, key_hash)
        
        # If reached the end of the list, loop back around to index 0 (The Circle!)
        if idx == len(self.ring):
            idx = 0
            
        return self.vnodes[self.ring[idx]]


if __name__ == "__main__":
    # Initialize ring with 3 virtual nodes per server for easy visualization
    ring = ConsistentHashRing(replicas=3)
    
    ring.add_server("Server_A")
    ring.add_server("Server_B")
    ring.add_server("Server_C")

    user_keys = ["user_122", "user_1024", "order_9982", "session_xyz", "product_456"]
    
    print("--- Initial Key Distribution ---")
    for key in user_keys:
        target_server = ring.get_server(key)
        print(f"Key {key} mapped to {target_server}")


    print("\n Server_B crashed! Removing it from the cluster...")
    ring.remove_server("Server_B")

    print("\n--- Key Distribution After Server_B Crash ---")
    for key in user_keys:
        target_server = ring.get_server(key)
        print(f"Key {key} gracefully re-routed to {target_server}")