# validation.py

from django.core.exceptions import ValidationError
from .models import FilingInformation

class XBRLValidator:
    """
    Utility class for validating XBRL data before processing
    """
    
    @staticmethod
    def validate_filing_information(data):
        """
        Validate filing information data
        
        Args:
            data (dict): Filing information data
            
        Returns:
            tuple: (is_valid, errors)
        """
        errors = {}
        
        # Required fields
        required_fields = [
            'company_name', 'unique_entity_number', 'current_period_start', 
            'current_period_end', 'xbrl_filing_type', 'financial_statement_type',
            'accounting_standard', 'authorisation_date', 'financial_position_type'
        ]
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = f"{field} is required"
        
        # UEN validation
        if 'unique_entity_number' in data and data['unique_entity_number']:
            uen = data['unique_entity_number']
            if not (len(uen) == 10 and uen[:9].isdigit() and uen[9].isalpha() and uen[9].isupper()):
                errors['unique_entity_number'] = "UEN must be 9 digits followed by 1 uppercase letter"
        
        # Financial consistency checks
        if 'current_period_start' in data and 'current_period_end' in data:
            try:
                start = data['current_period_start']
                end = data['current_period_end']
                
                # Check if end date is after start date (assuming ISO format YYYY-MM-DD)
                if start > end:
                    errors['current_period_end'] = "Current period end date must be after start date"
            except (ValueError, TypeError):
                errors['current_period_dates'] = "Invalid date format. Use YYYY-MM-DD format."
        
        return (len(errors) == 0, errors)
    
    @staticmethod
    def validate_financial_position(data):
        """
        Validate statement of financial position data
        
        Args:
            data (dict): Financial position data
            
        Returns:
            tuple: (is_valid, errors)
        """
        errors = {}
        
        # Validate totals match
        try:
            # Current assets total check
            if 'current_assets' in data:
                current_assets = data['current_assets']
                calculated_total = 0
                for key, value in current_assets.items():
                    if key != 'total_current_assets' and value is not None:
                        calculated_total += value
                
                if abs(calculated_total - current_assets.get('total_current_assets', 0)) > 0.01:
                    errors['current_assets_total'] = "Current assets total doesn't match sum of components"
            
            # Non-current assets total check
            if 'noncurrent_assets' in data:
                noncurrent_assets = data['noncurrent_assets']
                calculated_total = 0
                for key, value in noncurrent_assets.items():
                    if key != 'total_noncurrent_assets' and value is not None:
                        calculated_total += value
                
                if abs(calculated_total - noncurrent_assets.get('total_noncurrent_assets', 0)) > 0.01:
                    errors['noncurrent_assets_total'] = "Non-current assets total doesn't match sum of components"
            
            # Current liabilities total check
            if 'current_liabilities' in data:
                current_liabilities = data['current_liabilities']
                calculated_total = 0
                for key, value in current_liabilities.items():
                    if key != 'total_current_liabilities' and value is not None:
                        calculated_total += value
                
                if abs(calculated_total - current_liabilities.get('total_current_liabilities', 0)) > 0.01:
                    errors['current_liabilities_total'] = "Current liabilities total doesn't match sum of components"
            
            # Non-current liabilities total check
            if 'noncurrent_liabilities' in data:
                noncurrent_liabilities = data['noncurrent_liabilities']
                calculated_total = 0
                for key, value in noncurrent_liabilities.items():
                    if key != 'total_noncurrent_liabilities' and value is not None:
                        calculated_total += value
                
                if abs(calculated_total - noncurrent_liabilities.get('total_noncurrent_liabilities', 0)) > 0.01:
                    errors['noncurrent_liabilities_total'] = "Non-current liabilities total doesn't match sum of components"
            
            # Check if total assets = total liabilities + equity
            if 'total_assets' in data and 'total_liabilities' in data and 'equity' in data and 'total_equity' in data['equity']:
                total_assets = data['total_assets']
                total_liabilities = data['total_liabilities']
                total_equity = data['equity']['total_equity']
                
                if abs(total_assets - (total_liabilities + total_equity)) > 0.01:
                    errors['balance_sheet_equation'] = "Total assets must equal total liabilities plus equity"
            
        except (TypeError, ValueError) as e:
            errors['calculation_error'] = f"Error in financial calculations: {str(e)}"
        
        return (len(errors) == 0, errors)
    
    @staticmethod
    def validate_xbrl_data(data):
        """
        Validate full XBRL data
        
        Args:
            data (dict): XBRL data
            
        Returns:
            tuple: (is_valid, errors)
        """
        all_errors = {}
        
        # Validate filing information
        if 'filing_information' in data:
            valid, errors = XBRLValidator.validate_filing_information(data['filing_information'])
            if not valid:
                all_errors['filing_information'] = errors
        else:
            all_errors['filing_information'] = "Filing information is required"
        
        # Validate statement of financial position
        if 'statement_of_financial_position' in data:
            valid, errors = XBRLValidator.validate_financial_position(data['statement_of_financial_position'])
            if not valid:
                all_errors['statement_of_financial_position'] = errors
        else:
            all_errors['statement_of_financial_position'] = "Statement of financial position is required"
        
        # Add additional validation for other sections as needed
        
        return (len(all_errors) == 0, all_errors)