#include <iostream>
#include <cstring>
int main() {
    char buffer[8];
    strcpy(buffer, "This long string overflows buffer!"); // Stack overflow smell
    int* leak = new int(10); // Memory leak smell
    return 0;
}