// XFAIL: Linux
// RUN: %hc %s -c -o %t_file1.out && %hc %s %t_file1.out -o %t.out && %t.out

#include "grid_launch.h"

__KERNEL void foo(grid_launch_parm lp, int* a)
{
  int x = lp.threadId.x + lp.groupDim.x*lp.groupId.x;
  a[x] = x;
}

int main()
{
  int size = 1000;

  int* a = (int*)malloc(sizeof(int)*size);

  grid_launch_parm lp;
  grid_launch_init(&lp);

  lp.groupDim = uint3(size);

  hc::completion_future cf;
  lp.cf = &cf;
  foo(lp, a);
  lp.cf->wait();

  int ret = 0;
  for(int i = 0; i < size; ++i)
  {
    if(a[i] != i)
    {
      ret = 1;
      if(i < 64)
        printf("%d %d\n", a[i], i);
      break;
    }
  }

  return ret;
}
