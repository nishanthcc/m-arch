class PaymentGateway:
    def process_charge(self, token, amount):
        # Payment charge logic
        return {'status': 'success', 'amount': amount}
