def ask_for_columns(df):
    print("\nAvailable columns:")
    print(df.columns.tolist())

    predictors = input("\nEnter predictor columns (comma separated): ").split(",")
    predictors = [p.strip() for p in predictors]

    target = input("Enter target column: ").strip()

    return predictors, target
#script callers 
#for scenario
 #predictors, target = ask_for_columns(df)
#for relation
  #predictors, target = ask_for_columns(df)
#for comparison
#print(df.columns.tolist())
#group_col = input("Enter grouping column: ").strip()
#metric = input("Enter metric column: ").strip()
#group_a = input("Enter first group value: ").strip()
#group_b = input("Enter second group value: ").strip()
