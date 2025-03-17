# serializers.py
from rest_framework import serializers
from .models import (
    FilingInformation, DirectorsStatement, AuditReport, 
    CurrentAssets, MappingInput, NonCurrentAssets, CurrentLiabilities, 
    NonCurrentLiabilities, Equity, StatementOfFinancialPosition,
    IncomeStatement, TradeAndOtherReceivables, Revenue, Notes, PartialXBRL
)


class MappingInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = MappingInput
        fields = '__all__'  # Include all fields (id, content)
        
class FilingInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilingInformation
        fields = '__all__'

class DirectorsStatementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DirectorsStatement
        fields = '__all__'

class AuditReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditReport
        fields = '__all__'

class CurrentAssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrentAssets
        fields = '__all__'

class NonCurrentAssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NonCurrentAssets
        fields = '__all__'

class CurrentLiabilitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrentLiabilities
        fields = '__all__'

class NonCurrentLiabilitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = NonCurrentLiabilities
        fields = '__all__'

class EquitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Equity
        fields = '__all__'

class StatementOfFinancialPositionSerializer(serializers.ModelSerializer):
    current_assets = CurrentAssetsSerializer()
    noncurrent_assets = NonCurrentAssetsSerializer()
    current_liabilities = CurrentLiabilitiesSerializer()
    noncurrent_liabilities = NonCurrentLiabilitiesSerializer()
    equity = EquitySerializer()

    class Meta:
        model = StatementOfFinancialPosition
        fields = '__all__'

class IncomeStatementSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeStatement
        fields = '__all__'

class TradeAndOtherReceivablesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeAndOtherReceivables
        fields = '__all__'

class RevenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Revenue
        fields = '__all__'

class NotesSerializer(serializers.ModelSerializer):
    trade_and_other_receivables = TradeAndOtherReceivablesSerializer()
    trade_and_other_payables = TradeAndOtherReceivablesSerializer()

    class Meta:
        model = Notes
        fields = '__all__'

class PartialXBRLSerializer(serializers.ModelSerializer):
    filing_information = FilingInformationSerializer()
    directors_statement = DirectorsStatementSerializer()
    audit_report = AuditReportSerializer()
    statement_of_financial_position = StatementOfFinancialPositionSerializer()
    income_statement = IncomeStatementSerializer()
    notes = NotesSerializer()

    class Meta:
        model = PartialXBRL
        fields = '__all__'

    def create(self, validated_data):
        # Extract nested data
        filing_info_data = validated_data.pop('filing_information')
        directors_statement_data = validated_data.pop('directors_statement')
        audit_report_data = validated_data.pop('audit_report')
        
        # Extract statement of financial position data and its nested components
        sof_position_data = validated_data.pop('statement_of_financial_position')
        current_assets_data = sof_position_data.pop('current_assets')
        noncurrent_assets_data = sof_position_data.pop('noncurrent_assets')
        current_liabilities_data = sof_position_data.pop('current_liabilities')
        noncurrent_liabilities_data = sof_position_data.pop('noncurrent_liabilities')
        equity_data = sof_position_data.pop('equity')
        
        income_statement_data = validated_data.pop('income_statement')
        
        # Extract notes data and its nested components
        notes_data = validated_data.pop('notes')
        trade_receivables_data = notes_data.pop('trade_and_other_receivables')
        trade_payables_data = notes_data.pop('trade_and_other_payables')

        # Create filing information first
        filing_info = FilingInformation.objects.create(**filing_info_data)
        
        # Create directors statement and audit report
        directors_statement = DirectorsStatement.objects.create(filing=filing_info, **directors_statement_data)
        audit_report = AuditReport.objects.create(filing=filing_info, **audit_report_data)
        
        # Create financial position components
        current_assets = CurrentAssets.objects.create(filing=filing_info, **current_assets_data)
        noncurrent_assets = NonCurrentAssets.objects.create(filing=filing_info, **noncurrent_assets_data)
        current_liabilities = CurrentLiabilities.objects.create(filing=filing_info, **current_liabilities_data)
        noncurrent_liabilities = NonCurrentLiabilities.objects.create(filing=filing_info, **noncurrent_liabilities_data)
        equity = Equity.objects.create(filing=filing_info, **equity_data)
        
        # Create statement of financial position
        sof_position = StatementOfFinancialPosition.objects.create(
            filing=filing_info,
            current_assets=current_assets,
            noncurrent_assets=noncurrent_assets,
            current_liabilities=current_liabilities,
            noncurrent_liabilities=noncurrent_liabilities,
            equity=equity,
            **sof_position_data
        )
        
        # Create income statement
        income_statement = IncomeStatement.objects.create(filing=filing_info, **income_statement_data)
        
        # Create notes components
        trade_receivables = TradeAndOtherReceivables.objects.create(filing=filing_info, **trade_receivables_data)
        trade_payables = TradeAndOtherReceivables.objects.create(filing=filing_info, **trade_payables_data)
        
        # Create notes
        notes = Notes.objects.create(
            filing=filing_info,
            trade_and_other_receivables=trade_receivables,
            trade_and_other_payables=trade_payables,
            **notes_data
        )
        
        # Finally create the partial XBRL object
        xbrl = PartialXBRL.objects.create(
            filing_information=filing_info,
            directors_statement=directors_statement,
            audit_report=audit_report,
            statement_of_financial_position=sof_position,
            income_statement=income_statement,
            notes=notes,
            **validated_data
        )
        
        return xbrl

    def update(self, instance, validated_data):
        # Similar to create but update existing instances
        # This would be a more complex implementation with many nested updates
        # For brevity, only showing the pattern
        
        # Update filing information
        filing_info_data = validated_data.pop('filing_information', {})
        filing_info = instance.filing_information
        for attr, value in filing_info_data.items():
            setattr(filing_info, attr, value)
        filing_info.save()
        
        # Similar updates would be needed for all other nested objects
        
        return instance