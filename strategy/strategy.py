class Strategy:
    def __init__(self):
        # El 0.02% (2 bps) que dicen las reglas. Usamos 0.0002 como decimal.
        self.fee = 0.0002
        self.initialized = True
        
    def on_data(self, market_data, balances):
        # Lista para guardar las operaciones que ejecutaremos en este tick
        orders = []
        
        # Necesitamos que los 3 pares existan en el snapshot actual
        if not all(pair in market_data for pair in ["token_1/fiat", "token_2/fiat", "token_1/token_2"]):
            return orders

        # Precios actuales (Market orders se ejecutan al 'close')
        p_t1_fiat = market_data["token_1/fiat"]["close"]
        p_t2_fiat = market_data["token_2/fiat"]["close"]
        p_t1_t2 = market_data["token_1/token_2"]["close"]

        # --- CICLO 1: Fiat -> Token_1 -> Token_2 -> Fiat ---
        # Si empezamos con 1 unidad de Fiat:
        qty_t1 = (1.0 / p_t1_fiat) * (1 - self.fee)
        qty_t2 = (qty_t1 * p_t1_t2) * (1 - self.fee) # Vendemos t1 para conseguir t2
        fiat_return_cycle_1 = (qty_t2 * p_t2_fiat) * (1 - self.fee)

        # --- CICLO 2: Fiat -> Token_2 -> Token_1 -> Fiat ---
        # Si empezamos con 1 unidad de Fiat:
        qty_t2_c2 = (1.0 / p_t2_fiat) * (1 - self.fee)
        qty_t1_c2 = (qty_t2_c2 / p_t1_t2) * (1 - self.fee) # Compramos t1 pagando con t2
        fiat_return_cycle_2 = (qty_t1_c2 * p_t1_fiat) * (1 - self.fee)

        # Usamos una cantidad base de Fiat para operar (ajusta si tienes más o menos saldo inicial)
        trade_amount_fiat = 1000.0 

        # Evaluamos Ciclo 1 (Rentabilidad > 1.0 significa beneficio puro tras comisiones)
        if fiat_return_cycle_1 > 1.00001 and balances.get("fiat", 0) >= trade_amount_fiat:
            
            q_step1 = trade_amount_fiat / p_t1_fiat # Cuánto t1 compramos
            q_step2 = q_step1 * (1 - self.fee)      # Vendemos el t1 por t2
            q_step3 = (q_step2 * p_t1_t2) * (1 - self.fee) # Vendemos el t2 por fiat
            
            orders = [
                {"pair": "token_1/fiat", "side": "buy", "qty": q_step1},
                {"pair": "token_1/token_2", "side": "sell", "qty": q_step2},
                {"pair": "token_2/fiat", "side": "sell", "qty": q_step3}
            ]
            return orders

        # Evaluamos Ciclo 2
        elif fiat_return_cycle_2 > 1.00001 and balances.get("fiat", 0) >= trade_amount_fiat:
            
            q_step1 = trade_amount_fiat / p_t2_fiat # Cuánto t2 compramos
            q_step2 = q_step1 * (1 - self.fee)      # Compramos t1 pagando con t2
            q_step3 = (q_step2 / p_t1_t2) * (1 - self.fee) # Vendemos el t1 por fiat
            
            orders = [
                {"pair": "token_2/fiat", "side": "buy", "qty": q_step1},
                {"pair": "token_1/token_2", "side": "buy", "qty": q_step3}, # Par cruzado
                {"pair": "token_1/fiat", "side": "sell", "qty": q_step3}
            ]
            return orders

        return orders