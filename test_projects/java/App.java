public class App {
    private String secret = "AIzaSyJavaSecretKey";
    public void execute(String cmd) {
        // Bug smell
        System.out.println("cmd: " + cmd);
        int[] arr = new int[5];
        arr[10] = 5; // Array index out of bounds
    }
}