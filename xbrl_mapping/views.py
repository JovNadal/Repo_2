# views.py (enhanced)
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view as api_decorator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
from xbrl_mapping.models import MappingInput, PartialXBRL
from .serializers import MappingInputSerializer, PartialXBRLSerializer
from .json_mapper import XBRLJSONMapper
from rest_framework.views import APIView

class PartialXBRLViewSet(viewsets.ModelViewSet):
    """
    API endpoint for XBRL data management
    """
    queryset = PartialXBRL.objects.all()
    serializer_class = PartialXBRLSerializer
    
class MappingInputView(APIView):
    def post(self, request):
        serializer = MappingInputSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Save the validated data into the database
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        mapping_inputs = MappingInput.objects.all()  # Get all records
        serializer = MappingInputSerializer(mapping_inputs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    #def get(self, request, mapping_id):
        #mapping_instance = get_object_or_404(MappingInput, id=mapping_id)
        #return Response({"id": str(mapping_instance.id), "content": mapping_instance.content})


FIELD_MAPPING = {
    "WhetherTheFinancialStatementsArePreparedOnGoingConcernBasis": "is_going_concern",
    "WhetherThereAreAnyChangesToComparativeAmounts": "has_comparative_changes",
    "DescriptionOfPresentationCurrency": "presentation_currency",
    "DescriptionOfFunctionalCurrency": "functional_currency",
    "TypeOfXBRLFiling": "xbrl_filing_type",
    "TypeOfStatementOfFinancialPosition": "financial_position_type",
    "TypeOfAccountingStandardUsedToPrepareFinancialStatements": "accounting_standard",
    "NatureOfFinancialStatementsCompanyLevelOrConsolidated": "financial_statement_type",
    "DateOfAuthorisationForIssueOfFinancialStatements": "authorisation_date"
}

def normalize_filing_information(data):
    """Renames old field names to match Django model fields."""
    normalized_data = {}
    for key, value in data.items():
        new_key = FIELD_MAPPING.get(key, key)  # Replace if mapping exists, otherwise keep original
        normalized_data[new_key] = value
    return normalized_data

@api_decorator(['POST'])
def xbrl_mapping_api(request):
    """
    API to handle full XBRL Mapping JSON input and output.
    Normalizes old JSON field names before saving.
    """
    if request.method == 'POST':
        # Normalize the JSON field names
        if "filing_information" in request.data:
            request.data["filing_information"] = normalize_filing_information(request.data["filing_information"])

        # Validate and save
        serializer = PartialXBRLSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "XBRL Mapping saved successfully", "data": serializer.data}, status=201)
        
        return Response(serializer.errors, status=400)

@api_decorator(['POST'])
def upload_xbrl_json(request):
    """
    Endpoint to upload XBRL data in JSON format
    """
    try:
        serializer = PartialXBRLSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_decorator(['GET'])
def get_xbrl_by_uen(request, uen):
    """
    Retrieve XBRL data by UEN (Unique Entity Number)
    """
    try:
        xbrl = PartialXBRL.objects.get(filing_information__unique_entity_number=uen)
        serializer = PartialXBRLSerializer(xbrl)
        return Response(serializer.data)
    except PartialXBRL.DoesNotExist:
        return Response({"error": "XBRL data not found for the specified UEN"}, 
                        status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
def direct_json_import(request):
    """
    Direct import endpoint using the XBRLJSONMapper
    
    This endpoint bypasses Django REST Framework serialization 
    and uses our custom mapper directly
    """
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request body
            input_json = json.loads(request.body)
            
            # Transform the JSON data to match the expected format
            transformed_json = transform_json_for_xbrl_mapper(input_json)
            
            # Use the mapper to create the XBRL object
            xbrl = XBRLJSONMapper.map_json_to_xbrl(transformed_json)
            
            # Return the created object as JSON
            result = XBRLJSONMapper.export_xbrl_to_json(xbrl)
            return JsonResponse({"status": "success", "id": xbrl.id, "data": result})
        except ValueError as e:
            return JsonResponse({"status": "error", "message": f"Invalid JSON format: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    
    return JsonResponse({"error": "Only POST method is allowed"}, status=405)

def transform_json_for_xbrl_mapper(input_json):
    """
    Transforms the input JSON to match the expected format for XBRLJSONMapper
    
    Args:
        input_json (dict): The input JSON data in camelCase format
        
    Returns:
        dict: The transformed JSON data in snake_case format
    """
    # Helper function to convert camelCase to snake_case
    def camel_to_snake(name):
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    # Recursively transform keys in a dictionary
    def transform_dict(d):
        if not isinstance(d, dict):
            return d
        return {camel_to_snake(k): transform_dict(v) for k, v in d.items()}
    
    # Transform the main JSON structure
    transformed = {}
    
    # Transform filing information
    transformed['filing_information'] = transform_dict(input_json.get('filingInformation', {}))
    
    # Transform directors statement
    transformed['directors_statement'] = transform_dict(input_json.get('directorsStatement', {}))
    
    # Transform audit report
    transformed['audit_report'] = transform_dict(input_json.get('auditReport', {}))
    
    # Transform statement of financial position
    fin_position = input_json.get('statementOfFinancialPosition', {})
    transformed['statement_of_financial_position'] = {
        'current_assets': transform_dict(fin_position.get('currentAssets', {})),
        'noncurrent_assets': transform_dict(fin_position.get('nonCurrentAssets', {})),
        'current_liabilities': transform_dict(fin_position.get('currentLiabilities', {})),
        'noncurrent_liabilities': transform_dict(fin_position.get('nonCurrentLiabilities', {})),
        'equity': transform_dict(fin_position.get('equity', {})),
        'total_assets': fin_position.get('Assets', 0),
        'total_liabilities': fin_position.get('Liabilities', 0)
    }
    
    # Transform income statement
    transformed['income_statement'] = transform_dict(input_json.get('incomeStatement', {}))
    
    # Transform notes
    notes = input_json.get('notes', {})
    transformed['notes'] = {
        'trade_and_other_receivables': transform_dict(notes.get('tradeAndOtherReceivables', {})),
        'trade_and_other_payables': transform_dict(notes.get('tradeAndOtherPayables', {}))
    }
    
    return transformed

@api_decorator(['GET'])
def export_xbrl_json(request, pk):
    """
    Export XBRL data to JSON format
    """
    try:
        xbrl = PartialXBRL.objects.get(pk=pk)
        result = XBRLJSONMapper.export_xbrl_to_json(xbrl)
        return Response(result)
    except PartialXBRL.DoesNotExist:
        return Response({"error": "XBRL data not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_decorator(['POST'])
def validate_xbrl_json(request):
    """
    Validate XBRL JSON data without saving to database
    """
    try:
        serializer = PartialXBRLSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"status": "valid", "message": "The provided JSON is valid XBRL data"})
        return Response({"status": "invalid", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_decorator(['GET'])
def get_xbrl_template(request):
    """
    Get an empty XBRL JSON template
    """
    template = {
        "filing_information": {
            "company_name": "",
            "unique_entity_number": "",
            "current_period_start": "YYYY-MM-DD",
            "current_period_end": "YYYY-MM-DD",
            "prior_period_start": "YYYY-MM-DD",
            "xbrl_filing_type": "",
            "financial_statement_type": "",
            "accounting_standard": "",
            "authorisation_date": "YYYY-MM-DD",
            "financial_position_type": "",
            "is_going_concern": True,
            "has_comparative_changes": False,
            "presentation_currency": "",
            "functional_currency": "",
            "rounding_level": "",
            "entity_operations_description": "",
            "principal_place_of_business": "",
            "has_more_than_50_employees": False,
            "parent_entity_name": "",
            "ultimate_parent_name": "",
            "taxonomy_version": "2022.2",
            "xbrl_software": "",
            "xbrl_preparation_method": ""
        },
        "directors_statement": {
            "directors_opinion_true_fair_view": True,
            "reasonable_grounds_company_debts": True
        },
        "audit_report": {
            "audit_opinion": "",
            "auditing_standards": "",
            "material_uncertainty_going_concern": False,
            "proper_accounting_records": True
        },
        "statement_of_financial_position": {
            "total_assets": 0.0,
            "total_liabilities": 0.0,
            "current_assets": {
                "cash_and_bank_balances": 0.0,
                "trade_and_other_receivables": 0.0,
                "current_finance_lease_receivables": 0.0,
                "current_derivative_financial_assets": 0.0,
                "current_financial_assets_at_fair_value": 0.0,
                "other_current_financial_assets": 0.0,
                "development_properties": 0.0,
                "inventories": 0.0,
                "other_current_nonfinancial_assets": 0.0,
                "held_for_sale_assets": 0.0,
                "total_current_assets": 0.0
            },
            "noncurrent_assets": {
                "trade_and_other_receivables": 0.0,
                "noncurrent_finance_lease_receivables": 0.0,
                "noncurrent_derivative_financial_assets": 0.0,
                "noncurrent_financial_assets_at_fair_value": 0.0,
                "other_noncurrent_financial_assets": 0.0,
                "property_plant_equipment": 0.0,
                "investment_properties": 0.0,
                "goodwill": 0.0,
                "intangible_assets": 0.0,
                "investments_in_entities": 0.0,
                "deferred_tax_assets": 0.0,
                "other_noncurrent_nonfinancial_assets": 0.0,
                "total_noncurrent_assets": 0.0
            },
            "current_liabilities": {
                "trade_and_other_payables": 0.0,
                "current_loans_and_borrowings": 0.0,
                "current_financial_liabilities_at_fair_value": 0.0,
                "current_finance_lease_liabilities": 0.0,
                "other_current_financial_liabilities": 0.0,
                "current_income_tax_liabilities": 0.0,
                "current_provisions": 0.0,
                "other_current_nonfinancial_liabilities": 0.0,
                "liabilities_held_for_sale": 0.0,
                "total_current_liabilities": 0.0
            },
            "noncurrent_liabilities": {
                "trade_and_other_payables": 0.0,
                "noncurrent_loans_and_borrowings": 0.0,
                "noncurrent_financial_liabilities_at_fair_value": 0.0,
                "noncurrent_finance_lease_liabilities": 0.0,
                "other_noncurrent_financial_liabilities": 0.0,
                "deferred_tax_liabilities": 0.0,
                "noncurrent_provisions": 0.0,
                "other_noncurrent_nonfinancial_liabilities": 0.0,
                "total_noncurrent_liabilities": 0.0
            },
            "equity": {
                "share_capital": 0.0,
                "treasury_shares": 0.0,
                "accumulated_profits_losses": 0.0,
                "other_reserves": 0.0,
                "noncontrolling_interests": 0.0,
                "total_equity": 0.0
            }
        },
        "income_statement": {
            "revenue": 0.0,
            "other_income": 0.0,
            "employee_expenses": 0.0,
            "depreciation_expense": 0.0,
            "amortisation_expense": 0.0,
            "repairs_and_maintenance_expense": 0.0,
            "sales_and_marketing_expense": 0.0,
            "other_expenses_by_nature": 0.0,
            "other_gains_losses": 0.0,
            "finance_costs": 0.0,
            "share_of_profit_loss_of_associates_and_joint_ventures_accounted_for_using_equity_method": 0.0,
            "profit_loss_before_taxation": 0.0,
            "tax_expense_benefit_continuing_operations": 0.0,
            "profit_loss_from_discontinued_operations": 0.0,
            "profit_loss": 0.0,
            "profit_loss_attributable_to_owners_of_company": 0.0,
            "profit_loss_attributable_to_noncontrolling_interests": 0.0
        },
        "notes": {
            "trade_and_other_receivables": {
                "receivables_from_third_parties": 0.0,
                "receivables_from_related_parties": 0.0,
                "unbilled_receivables": 0.0,
                "other_receivables": 0.0,
                "total_trade_and_other_receivables": 0.0
            },
            "trade_and_other_payables": {
                "receivables_from_third_parties": 0.0,
                "receivables_from_related_parties": 0.0,
                "unbilled_receivables": 0.0,
                "other_receivables": 0.0,
                "total_trade_and_other_receivables": 0.0
            }
        }
    }
    
    return Response(template)

@api_decorator(['POST'])
def bulk_operations(request):
    """
    Handle bulk operations for XBRL data
    """
    operation = request.data.get('operation')
    
    if operation == 'import':
        items = request.data.get('items', [])
        results = []
        
        for item in items:
            try:
                xbrl = XBRLJSONMapper.map_json_to_xbrl(item)
                results.append({
                    'status': 'success',
                    'id': xbrl.id,
                    'uen': xbrl.filing_information.unique_entity_number
                })
            except Exception as e:
                results.append({
                    'status': 'error',
                    'message': str(e),
                    'data': item.get('filing_information', {}).get('unique_entity_number', 'Unknown UEN')
                })
        
        return Response({'results': results})
    
    elif operation == 'export':
        uens = request.data.get('uens', [])
        results = []
        
        for uen in uens:
            try:
                xbrl = PartialXBRL.objects.get(filing_information__unique_entity_number=uen)
                data = XBRLJSONMapper.export_xbrl_to_json(xbrl)
                results.append({
                    'status': 'success',
                    'uen': uen,
                    'data': data
                })
            except PartialXBRL.DoesNotExist:
                results.append({
                    'status': 'error',
                    'message': f'XBRL data not found for UEN: {uen}',
                    'uen': uen
                })
        
        return Response({'results': results})
    
    elif operation == 'delete':
        uens = request.data.get('uens', [])
        results = []
        
        for uen in uens:
            try:
                xbrl = PartialXBRL.objects.get(filing_information__unique_entity_number=uen)
                filing_info = xbrl.filing_information
                xbrl.delete()
                filing_info.delete()  # Delete the parent filing information
                results.append({
                    'status': 'success',
                    'message': f'Successfully deleted XBRL data for UEN: {uen}',
                    'uen': uen
                })
            except PartialXBRL.DoesNotExist:
                results.append({
                    'status': 'error',
                    'message': f'XBRL data not found for UEN: {uen}',
                    'uen': uen
                })
        
        return Response({'results': results})
    
    return Response({'error': 'Invalid operation'}, status=status.HTTP_400_BAD_REQUEST)