# Exercise 5.4 - Is run A better than run B?
# Run from the root of the repository:  Rscript chapters/ch05/r/solutions/ex5_4_significance.R

binom.test(1, 5)$p.value    # 1 case for B out of 5 changed cases
