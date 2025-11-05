import numpy as np
from simplex import Simplex
from display import build_iteration_views, label_tableau, dataframe_to_text, problem_summary

c=[3,5]
A=[[1,0],[0,2],[3,2]]
b=[4,12,18]
steps, sol = Simplex(c,A,b)
print('steps:', len(steps))
print('solution:', sol)
views = build_iteration_views(steps,c,A,b)
print('views:', len(views))
for i,v in enumerate(views,1):
    print('ITER', i)
    print('Enter', v['entering'],'Leave', v['leaving'])
    print(dataframe_to_text(v['before_df']))
    print('after:')
    print(dataframe_to_text(v['after_df']))
    print()
print('Summary:')
print(problem_summary(c,A,b))
