import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
from accounts.models import BorrowerProfile, LedgerEntry
from loans.models import Loan


class MLRiskScorer:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def extract_features(self, borrower_profile):
        """Extract ML features from borrower profile"""
        user = borrower_profile.user
        
        # Basic features
        business_age = borrower_profile.business_age or 0
        wallet_balance = float(user.wallet.balance)
        
        # Transaction history
        tx_count = LedgerEntry.objects.filter(wallet=user.wallet).count()
        avg_tx_amount = LedgerEntry.objects.filter(
            wallet=user.wallet
        ).aggregate(avg=models.Avg('amount'))['avg'] or 0
        
        # Loan history
        past_loans = Loan.objects.filter(borrower=user, status='COMPLETED').count()
        defaulted_loans = Loan.objects.filter(borrower=user, status='DEFAULTED').count()
        
        return np.array([
            business_age,
            wallet_balance,
            tx_count,
            float(avg_tx_amount),
            past_loans,
            defaulted_loans,
            1 if borrower_profile.kyc_status == 'VERIFIED' else 0
        ]).reshape(1, -1)
    
    def train_model(self):
        """Train ML model on existing data"""
        profiles = BorrowerProfile.objects.all()
        if len(profiles) < 10:
            return False  # Need more data
        
        X = []
        y = []
        
        for profile in profiles:
            features = self.extract_features(profile).flatten()
            X.append(features)
            
            # Label: 1 if good borrower, 0 if bad
            defaulted = Loan.objects.filter(
                borrower=profile.user, 
                status='DEFAULTED'
            ).exists()
            y.append(0 if defaulted else 1)
        
        X = np.array(X)
        y = np.array(y)
        
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # Save model
        joblib.dump(self.model, 'risk_model.pkl')
        joblib.dump(self.scaler, 'risk_scaler.pkl')
        
        return True
    
    def predict_risk_score(self, borrower_profile):
        """Predict risk score using ML model"""
        if not self.is_trained:
            try:
                self.model = joblib.load('risk_model.pkl')
                self.scaler = joblib.load('risk_scaler.pkl')
                self.is_trained = True
            except:
                # Fallback to rule-based scoring
                from .scoring import calculate_risk_score
                return calculate_risk_score(borrower_profile)
        
        features = self.extract_features(borrower_profile)
        features_scaled = self.scaler.transform(features)
        
        # Get probability of being a good borrower
        prob = self.model.predict_proba(features_scaled)[0][1]
        
        # Convert to credit score (300-850)
        score = int(300 + (prob * 550))
        return max(300, min(850, score))


# Global ML scorer instance
ml_scorer = MLRiskScorer()