#include <iostream>					// 编译预处理命令
#include "sort_topk.h"
using namespace std;

#define MAXSIZE 100

int main()
{
	/*int n = 12;
	int arr[12] = { 8, 3, 6, 1, 68, 12 };*/

	int n, k;
	cin >> n >> k;
	if (n > MAXSIZE) return 0;

	int arr[MAXSIZE] = { 0 };
	for (int i = 0; i < n; ++i) {
		cin >> arr[i];
	}

    Sort_TopK(arr, n, k); 
	return 0;						
}