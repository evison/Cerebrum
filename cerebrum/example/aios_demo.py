from cerebrum import config
from cerebrum.client import Cerebrum
from cerebrum.llm.layer import LLMLayer
from cerebrum.memory.layer import MemoryLayer
from cerebrum.overrides.layer import OverridesLayer
from cerebrum.storage.layer import StorageLayer
from cerebrum.tool.layer import ToolLayer
import argparse
import os
import sys
from typing import Optional, Dict, Any


def setup_client(
    llm_name: str = "gemini-1.5-flash",
    root_dir: str = "root",
    memory_limit: int = 500*1024*1024,
    max_workers: int = 32
) -> Cerebrum:
    """Initialize and configure the Cerebrum client with specified parameters."""
    client = Cerebrum()
    config.global_client = client

    try:
        client.add_llm_layer(LLMLayer(llm_name=llm_name)) \
              .add_storage_layer(StorageLayer(root_dir=root_dir)) \
              .add_memory_layer(MemoryLayer(memory_limit=memory_limit)) \
              .add_tool_layer(ToolLayer()) \
              .override_scheduler(OverridesLayer(max_workers=max_workers))
        
        status = client.get_status()
        print("✅ Client initialized successfully")
        print("Status:", status)
        
        return client
    except Exception as e:
        print(f"❌ Failed to initialize client: {str(e)}")
        raise


def run_agent(
    client: Cerebrum,
    agent_path: str,
    task: str,
    timeout: int = 300
) -> Optional[Dict[str, Any]]:
    """Run an agent with the specified task and wait for results."""
    try:
        client.connect()
        print(f"🚀 Executing agent: {os.path.basename(agent_path)}")
        print(f"📋 Task: {task}")

        result = client.execute(agent_path, {"task": task})
        
        try:
            final_result = client.poll_agent(
                result["execution_id"],
                timeout=timeout
            )
            print("✅ Agent execution completed")
            return final_result
        except TimeoutError:
            print("⚠️ Agent execution timed out")
            return None
            
    except Exception as e:
        print(f"❌ Error during agent execution: {str(e)}")
        return None
    finally:
        client.cleanup()


def main():
    """Main entry point for the demo script."""
    parser = argparse.ArgumentParser(description="AIOS Agent Demo")
    parser.add_argument(
        "--llm", 
        default="gemini-1.5-flash",
        help="LLM model to use"
    )
    parser.add_argument(
        "--root-dir",
        default="root",
        help="Root directory for storage"
    )
    parser.add_argument(
        "--memory-limit",
        type=int,
        default=500*1024*1024,
        help="Memory limit in bytes"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=32,
        help="Maximum number of workers"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds"
    )
    parser.add_argument(
        "--agent",
        default="/Users/rama2r/Cerebrum/example/agents/academic_agent",
        help="Path to the agent to execute"
    )
    parser.add_argument(
        "task",
        nargs="?",
        default="Tell me what is the prollm paper mainly about?",
        help="Task for the agent to execute"
    )

    args = parser.parse_args()

    print("🔧 Starting AIOS Demo with configuration:")
    print(f"  LLM: {args.llm}")
    print(f"  Root Directory: {args.root_dir}")
    print(f"  Memory Limit: {args.memory_limit} bytes")
    print(f"  Max Workers: {args.max_workers}")
    print(f"  Timeout: {args.timeout} seconds")
    print(f"  Agent: {args.agent}")
    print(f"  Task: {args.task}")
    print("-" * 50)

    try:
        client = setup_client(
            llm_name=args.llm,
            root_dir=args.root_dir,
            memory_limit=args.memory_limit,
            max_workers=args.max_workers
        )

        result = run_agent(
            client=client,
            agent_path=args.agent,
            task=args.task,
            timeout=args.timeout
        )

        if result:
            print("\n📊 Final Result:")
            print(result)
            return 0
        return 1

    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())