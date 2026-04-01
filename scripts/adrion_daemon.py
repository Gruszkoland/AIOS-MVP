import os
import time
import logging
from datetime import datetime

# cieka do ADRION CORE
# Tu moemy doda autorelacj (G1)
import adrion_healer as healer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - HEALER_DAEMON - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def start_daemon(interval=3690): # Domylny interwa 3690 (Unity + Rhythm)
    logger.info(f"ADRION Autopoiesis (Self-Healing) Daemon started. Interval: {interval}s")
    h = healer.AdrionHealer()
    while True:
        try:
            h.run_cycle()
            logger.info(f"Cycle complete. Waiting {interval} seconds...")
            time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Daemon stopped by user.")
            break
        except Exception as e:
            logger.error(f"Error in healer cycle: {e}")
            time.sleep(60) # Czekaj 1 minut przed ponown prób

if __name__ == '__main__':
    start_daemon()
