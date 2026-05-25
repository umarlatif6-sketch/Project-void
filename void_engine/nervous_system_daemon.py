"""
Nervous System Daemon — PROJECT VOID

Background process that runs the autonomous nervous system continuously.
Manages agent lifecycle, handles signals, and maintains system health.

This daemon is the heartbeat of Project VOID. Once started, it never stops.
Agents wake, scan, decide, execute, report, and sleep in an endless cycle.
"""

import asyncio
import signal
import sys
import logging
import json
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/void_nervous_system.log'),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


class NervousSystemDaemon:
    """
    Daemon that runs the autonomous nervous system.
    
    Handles:
    - Startup and initialization
    - Signal handling (SIGTERM, SIGINT)
    - Health monitoring
    - Graceful shutdown
    - Error recovery
    """

    def __init__(self, cycle_interval: int = 300, max_retries: int = 3):
        self.cycle_interval = cycle_interval
        self.max_retries = max_retries
        self.nervous_system = None
        self.running = False
        self.retry_count = 0

    async def initialize(self) -> None:
        """Initialize the daemon and nervous system."""
        logger.info("Initializing Nervous System Daemon")
        
        try:
            # Import here to avoid circular imports
            from void_engine.autonomous_nervous_system import create_nervous_system
            from void_engine.chronicle import RootChronicle
            
            # Get Chronicle database
            chronicle_db = RootChronicle()
            
            # Create nervous system with four agents
            self.nervous_system = create_nervous_system(
                chronicle_db=chronicle_db,
                cycle_interval=self.cycle_interval,
            )
            
            logger.info("Nervous System initialized successfully")
            logger.info(f"Agents: {len(self.nervous_system.agents)}")
            logger.info(f"Cycle interval: {self.cycle_interval} seconds")
            
        except Exception as e:
            logger.error(f"Failed to initialize Nervous System: {e}")
            raise

    async def start(self) -> None:
        """Start the daemon and nervous system."""
        logger.info("Starting Nervous System Daemon")
        self.running = True
        
        # Register signal handlers
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, self._handle_signal, signal.SIGTERM)
        loop.add_signal_handler(signal.SIGINT, self._handle_signal, signal.SIGINT)
        
        try:
            await self.initialize()
            logger.info("Daemon ready. Starting nervous system...")
            await self.nervous_system.start()
        except Exception as e:
            logger.error(f"Fatal error in daemon: {e}")
            self.running = False
            raise

    def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle termination signals."""
        logger.info(f"Received signal {sig.name}")
        self.running = False
        
        # Schedule graceful shutdown
        asyncio.create_task(self._shutdown())

    async def _shutdown(self) -> None:
        """Gracefully shutdown the daemon."""
        logger.info("Shutting down Nervous System Daemon")
        
        if self.nervous_system:
            await self.nervous_system.stop()
        
        logger.info("Daemon shutdown complete")
        sys.exit(0)

    async def monitor_health(self) -> None:
        """Monitor system health and log status periodically."""
        while self.running:
            try:
                if self.nervous_system:
                    status = await self.nervous_system.get_status()
                    logger.info(f"Nervous System Status: {json.dumps(status, indent=2)}")
                    self.retry_count = 0
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                self.retry_count += 1
                
                if self.retry_count >= self.max_retries:
                    logger.error("Max retries exceeded. Shutting down.")
                    await self._shutdown()
                
                await asyncio.sleep(10)


async def run_daemon(cycle_interval: int = 300) -> None:
    """
    Run the Nervous System Daemon.
    
    Args:
        cycle_interval: Seconds between agent wake cycles
    """
    daemon = NervousSystemDaemon(cycle_interval=cycle_interval)
    
    # Create health monitoring task
    health_task = asyncio.create_task(daemon.monitor_health())
    
    try:
        await daemon.start()
    except KeyboardInterrupt:
        logger.info("Daemon interrupted by user")
    except Exception as e:
        logger.error(f"Daemon error: {e}")
    finally:
        health_task.cancel()
        try:
            await health_task
        except asyncio.CancelledError:
            pass


def main():
    """Entry point for the daemon."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Autonomous Nervous System Daemon for Project VOID"
    )
    parser.add_argument(
        '--cycle-interval',
        type=int,
        default=300,
        help='Seconds between agent wake cycles (default: 300)'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default='/tmp/void_nervous_system.log',
        help='Log file path'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("PROJECT VOID — AUTONOMOUS NERVOUS SYSTEM DAEMON")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now(timezone.utc).isoformat()}")
    logger.info(f"Cycle interval: {args.cycle_interval} seconds")
    logger.info(f"Log file: {args.log_file}")
    logger.info("=" * 80)
    
    try:
        asyncio.run(run_daemon(cycle_interval=args.cycle_interval))
    except KeyboardInterrupt:
        logger.info("Daemon terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
