from memory_system import MemorySystem

def test_memory_system():
    try:
        mem = MemorySystem()
        print("All memory systems initialized successfully!")
        mem.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_memory_system()






"""""
from memory_system import MemorySystem

def test_memory():
    try:
        mem = MemorySystem()
        print("✅ Memory system initialized successfully!")
        print(f"URI: {mem.uri}, User: {mem.user}")
        mem.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_memory()
    """