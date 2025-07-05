def calculate_tax(salary_components, other_income, deductions, age_group, financial_year):
    """Calculate tax liability under old and new regimes"""
    # Calculate total income
    total_salary = sum(salary_components.values())
    total_other_income = sum(other_income.values())
    gross_income = total_salary + total_other_income
    
    # Standard deductions
    std_deduction_old = 50000
    std_deduction_new = 75000
    
    # Calculate taxable income under old regime
    taxable_income_old = gross_income - std_deduction_old
    
    # Apply deductions (simplified - would need more comprehensive handling in production)
    total_deductions = sum(deductions.values())
    taxable_income_old -= min(total_deductions, 150000)  # Basic 80C limit
    
    # Calculate tax under old regime
    tax_old = calculate_tax_old_regime(taxable_income_old, age_group)
    
    # Calculate taxable income under new regime
    taxable_income_new = gross_income - std_deduction_new
    
    # Calculate tax under new regime
    tax_new = calculate_tax_new_regime(taxable_income_new)
    
    # Apply rebate if applicable (as per Budget 2025)
    if financial_year == '2025-26' and taxable_income_new <= 700000:
        tax_new = max(0, tax_new - 60000)  # Rebate of 60,000
    
    # Add cess (4%)
    tax_old *= 1.04
    tax_new *= 1.04
    
    return {
        'old_regime': {
            'taxable_income': taxable_income_old,
            'tax': tax_old,
            'effective_rate': (tax_old / gross_income * 100) if gross_income > 0 else 0
        },
        'new_regime': {
            'taxable_income': taxable_income_new,
            'tax': tax_new,
            'effective_rate': (tax_new / gross_income * 100) if gross_income > 0 else 0
        },
        'recommended_regime': 'new' if tax_new < tax_old else 'old',
        'savings': abs(tax_new - tax_old)
    }

def calculate_tax_old_regime(income, age_group):
    """Calculate tax as per old regime slabs"""
    if age_group == 'senior' and income <= 300000:
        return 0
    elif age_group == 'super_senior' and income <= 500000:
        return 0
    
    # Standard slabs for <60 years
    if income <= 250000:
        return 0
    elif income <= 500000:
        return (income - 250000) * 0.05
    elif income <= 1000000:
        return 12500 + (income - 500000) * 0.2
    else:
        return 112500 + (income - 1000000) * 0.3

def calculate_tax_new_regime(income):
    """Calculate tax as per new regime slabs (Budget 2025)"""
    if income <= 400000:
        return 0
    elif income <= 800000:
        return (income - 400000) * 0.05
    elif income <= 1200000:
        return 20000 + (income - 800000) * 0.1
    elif income <= 1600000:
        return 60000 + (income - 1200000) * 0.15
    elif income <= 2000000:
        return 120000 + (income - 1600000) * 0.2
    elif income <= 2400000:
        return 200000 + (income - 2000000) * 0.25
    else:
        return 300000 + (income - 2400000) * 0.3

def get_tax_saving_tips(current_deductions, income, age_group, model):
    """Get personalized tax saving tips using Gemini"""
    prompt = f"""Provide personalized tax saving tips for an Indian taxpayer with:
    - Annual income: ₹{income:,.2f}
    - Age group: {age_group}
    - Current deductions: {current_deductions}
    
    Suggest specific:
    1. Additional deductions they could claim
    2. Investment options based on their risk profile
    3. Any overlooked exemptions
    4. Last-minute tax saving options if applicable
    
    Format the response in HTML with clear headings."""
    
    response = model.generate_content(prompt)
    return response.text