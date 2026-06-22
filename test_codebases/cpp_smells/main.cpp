#include <iostream>
#include <cstring>

void process_input(const char* input) {
    char buffer[16];
    // Buffer overflow risk
    strcpy(buffer, input);
    std::cout << "Buffer: " << buffer << std::endl;
}

int main() {
    // Memory leak
    int* data = new int[100];
    process_input("This is a very long string that will overflow the buffer");
    return 0;
}