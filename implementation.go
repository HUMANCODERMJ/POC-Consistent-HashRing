package main

import (
	"fmt"
	"hash/crc32"
	"sort"
	"strconv"
)

type ConsistentHashRing struct {
	replicas int               // Number of virtual nodes per server
	ring     []uint32          // Sorted slice of virtual node hashes
	vnodes   map[uint32]string // Map: hash_value -> physical_server
}

func NewConsistentHashRing(replicas int) *ConsistentHashRing {
	return &ConsistentHashRing{
		replicas: replicas,
		vnodes:   make(map[uint32]string),
	}
}

// hash generates a uint32 position on the circle
func (c *ConsistentHashRing) hash(key string) uint32 {
	return crc32.ChecksumIEEE([]byte(key))
}

// AddServer inserts a physical server's virtual nodes into the ring
func (c *ConsistentHashRing) AddServer(server string) {
	for i := 0; i < c.replicas; i++ {
		vnodeKey := server + "_vnode_" + strconv.Itoa(i)
		vnodeHash := c.hash(vnodeKey)
		
		c.ring = append(c.ring, vnodeHash)
		c.vnodes[vnodeHash] = server
	}
	// Keep the ring sorted so we can use binary search later
	sort.Slice(c.ring, func(i, j int) bool { return c.ring[i] < c.ring[j] })
}

// GetServer finds the correct server clockwise for a given data key
func (c *ConsistentHashRing) GetServer(dataKey string) string {
	if len(c.ring) == 0 {
		return ""
	}

	keyHash := c.hash(dataKey)

	// Search finds the smallest index i where c.ring[i] >= keyHash
	idx := sort.Search(len(c.ring), func(i int) bool {
		return c.ring[i] >= keyHash
	})

	// If we hit the end of the slice, loop back around to index 0 (The Circle!)
	if idx == len(c.ring) {
		idx = 0
	}

	return c.vnodes[c.ring[idx]]
}

func main() {
	// Initialize ring with 3 virtual nodes per server
	ring := NewConsistentHashRing(3)

	ring.AddServer("Server_A")
	ring.AddServer("Server_B")
	ring.AddServer("Server_C")

	userKeys := []string{"user_manas", "user_1024", "order_9982", "session_xyz", "product_456"}

	fmt.Println("--- Initial Key Distribution (Go) ---")
	for _, key := range userKeys {
		targetServer := ring.GetServer(key)
		fmt.Printf(" Key '%s' mapped to  %s\n", key, targetServer)
	}
}