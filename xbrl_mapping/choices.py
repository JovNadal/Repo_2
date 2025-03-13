from django.db import models

class XBRLFiling(models.TextChoices):
    FULL = "Full", "Full"
    PARTIAL = "Partial", "Partial"

class FinancialStatementType(models.TextChoices):
    COMPANY = "Company", "Company"
    CONSOLIDATED = "Consolidated", "Consolidated"

class AccountingStandard(models.TextChoices):
    SFRS = "SFRS", "SFRS"
    SFRS_SE = "SFRS for SE", "SFRS for SE"
    IFRS = "IFRS", "IFRS"
    OTHER = "Other", "Other"

class StatementOfFinancialPositionType(models.TextChoices):
    CLASSIFIED = "Classified", "Classified"
    LIQUIDITY = "Liquidity-based", "Liquidity-based"

class RoundingLevel(models.TextChoices):
    THOUSANDS = "Thousands", "Thousands"
    MILLIONS = "Millions", "Millions"
    UNITS = "Units", "Units"

class XBRLPreparationMethod(models.TextChoices):
    AUTOMATED = "Automated", "Automated"
    MANUAL = "Manual", "Manual"
    HYBRID = "Hybrid", "Hybrid"

class AuditOpinion(models.TextChoices):
    UNQUALIFIED = "Unqualified", "Unqualified"
    QUALIFIED = "Qualified", "Qualified"
    ADVERSE = "Adverse", "Adverse"
    DISCLAIMER = "Disclaimer", "Disclaimer"
