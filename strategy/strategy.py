class Strategy:
    def __init__(self):
        # Usamos 3 puntos básicos (0.0003) como indica el justfile
        self.fee = 0.0003
        self.initialized = True
        
    def on_data(self, market_data, balances):
        # Definición de pares según los archivos que me mandaste
        t1_f = "token_1/fiat"      # ETH/USDT
        t2_f = "token_2/fiat"      # BTC/USDT
        t1_t2 = "token_1/token_2"  # ETH/BTC

        if not all(p in market_data for p in [t1_f, t2_f, t1_t2]):
            return []

        # Precios actuales
        p1 = market_data[t1_f]["close"]     # Precio ETH en USDT
        p2 = market_data[t2_f]["close"]     # Precio BTC en USDT
        p12 = market_data[t1_t2]["close"]   # Precio ETH en BTC

        # --- ESTRATEGIA: ARBITRAJE TRIANGULAR ---
        # Calculamos el retorno neto de los dos ciclos posibles (3 comisiones cada uno)
        # Factor de pérdida por comisiones: (1 - 0.0003)^3 ≈ 0.9991
        fee_factor = (1 - self.fee) ** 3

        # Ciclo A: USDT -> comprar ETH -> vender ETH por BTC -> vender BTC por USDT
        # Fórmula: (1/p1 * p12 * p2) * fee_factor
        rent_a = (p12 * p2 / p1) * fee_factor

        # Ciclo B: USDT -> comprar BTC -> comprar ETH con BTC -> vender ETH por USDT
        # Fórmula: (1/p2 / p12 * p1) * fee_factor
        rent_b = (p1 / (p2 * p12)) * fee_factor

        # Usamos el 95% del balance de USDT para dejar un margen de seguridad
        fiat_disponible = balances.get("fiat", 0)
        monto_operar = fiat_disponible * 0.95

        # Si el retorno es mayor a 1.0 (más un margen de seguridad de 0.01%)
        umbral = 1.0001

        # EJECUCIÓN CICLO A
        if rent_a > umbral and monto_operar > 10:
            q_eth = monto_operar / p1
            q_btc = q_eth * (1 - self.fee) * p12
            return [
                {"pair": t1_f, "side": "buy", "qty": q_eth},
                {"pair": t1_t2, "side": "sell", "qty": q_eth * (1 - self.fee)},
                {"pair": t2_f, "side": "sell", "qty": q_btc * (1 - self.fee)}
            ]

        # EJECUCIÓN CICLO B
        if rent_b > umbral and monto_operar > 10:
            q_btc = monto_operar / p2
            # Cuánto ETH compramos con ese BTC
            q_eth = (q_btc * (1 - self.fee)) / p12
            return [
                {"pair": t2_f, "side": "buy", "qty": q_btc},
                {"pair": t1_t2, "side": "buy", "qty": q_eth},
                {"pair": t1_f, "side": "sell", "qty": q_eth * (1 - self.fee)}
            ]

        return []