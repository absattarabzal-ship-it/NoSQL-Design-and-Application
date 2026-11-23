module com.example.university_lab13 {
    requires javafx.controls;
    requires javafx.fxml;


    opens com.example.university_lab13 to javafx.fxml;
    exports com.example.university_lab13;
}