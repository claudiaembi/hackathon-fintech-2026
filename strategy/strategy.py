class Strategy:
    def __init__(self):
        # El 0.02% (2 bps) que dicen las reglas
        self.fee = 0.0002
        self.initialized = True
        
    def on_data(self, market_data, balances):
        orders = []
        
        if not all(pair in market_data for pair in ["token_1/fiat", "token_2/fiat", "token_1/token_2"]):
            return orders

        p_t1_fiat = market_data["token_1/fiat"]["close"]
        p_t2_fiat = market_data["token_2/fiat"]["close"]
        p_t1_t2 = market_data["token_1/token_2"]["close"]

        # --- CICLO 1: Fiat -> Token_1 -> Token_2 -> Fiat ---
        qty_t1 = (1.0 / p_t1_fiat) * (1 - self.fee)
        qty_t2 = (qty_t1 * p_t1_t2) * (1 - self.fee) 
        fiat_return_cycle_1 = (qty_t2 * p_t2_fiat) * (1 - self.fee)

        # --- CICLO 2: Fiat -> Token_2 -> Token_1 -> Fiat ---
        qty_t2_c2 = (1.0 / p_t2_fiat) * (1 - self.fee)
        qty_t1_c2 = (qty_t2_c2 / p_t1_t2) * (1 - self.fee) 
        fiat_return_cycle_2 = (qty_t1_c2 * p_t1_fiat) * (1 - self.fee)

        # Cantidad fija y segura de 1000
        trade_amount_fiat = 1000.0 

        # Umbral seguro: 1.00001
        if fiat_return_cycle_1 > 1.00001 and balances.get("fiat", 0) >= trade_amount_fiat:
            q_step1 = trade_amount_fiat / p_t1_fiat 
            q_step2 = q_step1 * (1 - self.fee)      
            q_step3 = (q_step2 * p_t1_t2) * (1 - self.fee) 
            
            return [
                {"pair": "token_1/fiat", "side": "buy", "qty": q_step1},
                {"pair": "token_1/token_2", "side": "sell", "qty": q_step2},
                {"pair": "token_2/fiat", "side": "sell", "qty": q_step3}
            ]

        elif fiat_return_cycle_2 > 1.00001 and balances.get("fiat", 0) >= trade_amount_fiat:
            q_step1 = trade_amount_fiat / p_t2_fiat 
            q_step2 = q_step1 * (1 - self.fee)      
            q_step3 = (q_step2 / p_t1_t2) * (1 - self.fee) 
            
            return [
                {"pair": "token_2/fiat", "side": "buy", "qty": q_step1},
                {"pair": "token_1/token_2", "side": "buy", "qty": q_step3}, 
                {"pair": "token_1/fiat", "side": "sell", "qty": q_step3}
            ]

        return orders