"""
Loan Calculator Program

This program calculates:
1. Monthly EMI (Equated Monthly Installment)
2. Total Payment
3. Total Interest Paid

Inputs required:
- Loan Amount
- Annual Interest Rate (%)
- Loan Tenure (Years or Months)
"""

import math


def calculate_emi(principal: float, annual_rate: float, months: int) -> tuple:
    """
    Calculate EMI, total payment and total interest.

    Args:
        principal (float): Loan amount
        annual_rate (float): Annual interest rate in percentage
        months (int): Loan tenure in months

    Returns:
        tuple: (emi, total_payment, total_interest)
    """

    # Convert annual interest rate to monthly rate
    monthly_rate = annual_rate / (12 * 100)

    if monthly_rate == 0:
        emi = principal / months
    else:
        emi = (
            principal
            * monthly_rate
            * (1 + monthly_rate) ** months
            / ((1 + monthly_rate) ** months - 1)
        )

    total_payment = emi * months
    total_interest = total_payment - principal

    return emi, total_payment, total_interest


def get_loan_tenure() -> int:
    """
    Ask user whether tenure is in years or months
    and convert it to months.
    """

    while True:
        choice = input("Enter tenure type (Y for Years / M for Months): ").strip().upper()

        if choice == "Y":
            years = float(input("Enter loan tenure (years): "))
            return int(years * 12)

        elif choice == "M":
            months = int(input("Enter loan tenure (months): "))
            return months

        else:
            print("Invalid choice. Please enter Y or M.")


def main():
    """Main function to run Loan Calculator."""

    print("\n===== LOAN CALCULATOR =====\n")

    try:
        principal = float(input("Enter Loan Amount: "))
        annual_rate = float(input("Enter Annual Interest Rate (%): "))
        months = get_loan_tenure()

        emi, total_payment, total_interest = calculate_emi(
            principal, annual_rate, months
        )

        print("\n------ Loan Summary ------")
        print(f"Monthly EMI        : ₹{emi:,.2f}")
        print(f"Total Payment      : ₹{total_payment:,.2f}")
        print(f"Total Interest Paid: ₹{total_interest:,.2f}")

    except ValueError:
        print("Invalid input! Please enter numeric values.")


if __name__ == "__main__":
    main()