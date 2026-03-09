class Strategy:
    def __init__(self):
        # Fee real de 3 bps (0.0003)
        self.fee = 0.0003
        # Bajamos el umbral para capturar más volumen de operaciones
        self.min_profit_margin = 1.0002

    def on_data(self, market_data, balances):
        t1_f = "token_1/fiat"
        t2_f = "token_2/fiat"
        t1_t2 = "token_1/token_2"

        if not all(p in market_data for p in [t1_f, t2_f, t1_t2]):
            return []

        p1 = market_data[t1_f]["close"]
        p2 = market_data[t2_f]["close"]
        p12 = market_data[t1_t2]["close"]
        f = self.fee

        # Factor de comisiones para 3 saltos
        net_factor = (1 - f) ** 3

        # Cálculo de rentabilidad neta
        ret_A = (p12 * p2 / p1) * net_factor
        ret_B = (p1 / (p2 * p12)) * net_factor

        fiat_total = balances.get("fiat", 0)

        # --- LÓGICA DE ESCALAMIENTO DINÁMICO ---
        # Si la oportunidad es mejor, arriesgamos más capital
        max_ret = max(ret_A, ret_B)

        if max_ret > 1.0012:      # Oportunidad de Oro
            cap_pct = 0.90
        elif max_ret > 1.0006:    # Oportunidad Buena
            cap_pct = 0.70
        else:                     # Oportunidad Normal
            cap_pct = 0.40

        monto_fiat = fiat_total * cap_pct

        # --- EJECUCIÓN CICLO A ---
        if ret_A > self.min_profit_margin and fiat_total > 20:
            # Factor 0.999 de seguridad para evitar errores de balance
            q1 = (monto_fiat / (p1 * (1 + f))) * 0.999
            q1_net = q1 * (1 - f)
            q2_net = q1_net * p12 * (1 - f)

            return [
                {"pair": t1_f, "side": "buy", "qty": round(q1, 7)},
                {"pair": t1_t2, "side": "sell", "qty": round(q1_net, 7)},
                {"pair": t2_f, "side": "sell", "qty": round(q2_net, 7)}
            ]

        # --- EJECUCIÓN CICLO B ---
        elif ret_B > self.min_profit_margin and fiat_total > 20:
            q2 = (monto_fiat / (p2 * (1 + f))) * 0.999
            q2_net = q2 * (1 - f)
            q1_net = q2_net / (p12 * (1 + f))

            return [
                {"pair": t2_f, "side": "buy", "qty": round(q2, 7)},
                {"pair": t1_t2, "side": "buy", "qty": round(q1_net, 7)},
                {"pair": t1_f, "side": "sell", "qty": round(q1_net * (1 - f), 7)}
            ]

        return []