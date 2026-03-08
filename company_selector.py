import json
import random
import os
import logging
from datetime import datetime, timedelta
import config

logger = logging.getLogger(__name__)

class CompanySelector:
    def __init__(self):
        self.watchlist_path = config.WATCHLIST_FILE
        self.history_path = config.HISTORY_FILE

    def load_watchlist(self):
        try:
            with open(self.watchlist_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading watchlist: {e}")
            return []

    def load_history(self):
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_history(self, symbol):
        history = self.load_history()
        history[symbol] = datetime.now().isoformat()
        # Clean up old history (older than 30 days)
        cutoff = datetime.now() - timedelta(days=30)
        history = {s: d for s, d in history.items() if datetime.fromisoformat(d) > cutoff}
        
        with open(self.history_path, 'w') as f:
            json.dump(history, f)

    def is_recent(self, symbol, history):
        if symbol not in history:
            return False
        last_date = datetime.fromisoformat(history[symbol])
        return (datetime.now() - last_date).days < 7

    def select_company(self):
        watchlist = self.load_watchlist()
        history = self.load_history()
        
        # 70% chance to pick from watchlist
        if random.random() < 0.7 and watchlist:
            available = [c for c in watchlist if not self.is_recent(c['symbol'], history)]
            if available:
                selected = random.choice(available)
                logger.info(f"Selected from watchlist: {selected['symbol']}")
                return selected
        
        # 30% chance or fallback: pick from NSE (Mocked for now, usually requires scraping NSE top gainers)
        # In a real scenario, we'd fetch NSE top movers here.
        # For this implementation, we fallback to watchlist if NSE fetch fails or for simplicity.
        available = [c for c in watchlist if not self.is_recent(c['symbol'], history)]
        if not available:
            # If everything was picked recently, just pick the oldest one
            sorted_history = sorted(history.items(), key=lambda x: x[1])
            if sorted_history:
                symbol = sorted_history[0][0]
                selected = next((c for c in watchlist if c['symbol'] == symbol), watchlist[0])
            else:
                selected = random.choice(watchlist)
        else:
            selected = random.choice(available)
            
        logger.info(f"Selected company: {selected['symbol']}")
        return selected
