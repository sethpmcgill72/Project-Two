from PyQt6.QtWidgets import *
from gui import *
import csv
import os

class Logic(QMainWindow, Ui_MainWindow):
    MINIMUM_NAMES = 0
    MINIMUM_CANDIDATES = 2
    MAXIMUM_CANDIDATES = 5
    MAX_NAME_LENGTH = 20
    DEFAULT_VOTES = 0

    SETUP_WINDOW_INDEX = 0
    VOTING_WINDOW_INDEX = 1

    ERROR_COLOR = "color:red"
    GOOD_COLOR = "color:green"

    def __init__(self) -> None:
        """
        Sets up a new window, along with connections
        """
        super().__init__()
        self.setupUi(self)

        # instance variables
        self.__candidates : dict[str, int] = {} # key = candidate, value = number of votes.
        self.__voter_id : str = ""
        self.__voter_data : dict[str, str] = {} # key = ID, value = chosen candidate.

        # submit or cancel voting setup on button press.
        self.SubmitSetupButton.clicked.connect(lambda : self.__submit_setup())
        self.ClearButton.clicked.connect(lambda : self.__clear_setup_page())

        # submit vote or cancel/finish voting process on button press.
        self.SubmitVoteButton.clicked.connect(lambda : self.__submit_vote())
        self.CancelButton.clicked.connect(lambda : self.__cancel_voting())
        self.SaveButton.clicked.connect(lambda : self.__save_results())

        # clear errors when typing in an input box.
        self.CandidateNamesInput.textChanged.connect(lambda : self.SetupDisplay.clear())
        self.IDInput.textChanged.connect(lambda : self.VoteDisplay.clear())

    def __submit_setup(self) -> None:
        """
        Initiates voting process when pressing "Go Vote!". Sets up candidates and checks input, displaying
        errors if invalid input is detected.
        """
        try: # get candidate list.
            self.__set_candidates(self.CandidateNamesInput.text())

        except Exception as error:
            self.SetupDisplay.setText(str(error))
            self.SetupDisplay.setStyleSheet(self.ERROR_COLOR)

        else:
            self.__setup_voting_page()
            self.stackedWidget.setCurrentIndex(self.VOTING_WINDOW_INDEX)
            self.__clear_setup_page()

    def __setup_voting_page(self) -> None:
        """
        Dynamically creates radio boxes for each candidate that the user can then use to vote.
        """
        x_coordinate = 75
        width = 320
        height = 30
        y_coordinate = 110
        y_increment = 30
        candidate_number = 1

        for candidate in self.__get_candidates(): # creates radio buttons.
            radio = QRadioButton(parent=self.VotePage)
            radio.setGeometry(x_coordinate, y_coordinate, width, height)
            radio.setObjectName("CandidateRadio")
            radio.clicked.connect(lambda : self.VoteDisplay.clear())

            radio.setText(candidate)

            radio.show()
            y_coordinate += y_increment
            candidate_number += 1

    def __clear_setup_page(self) -> None:
        """
        Clears vote setup input fields, resets spin boxes and errors.
        """
        self.CandidateCount.setValue(self.MINIMUM_CANDIDATES)
        self.CandidateNamesInput.clear()

    def __submit_vote(self) -> None:
        """
        Submits the current voter's poll, and checks that this is not a repeat voter.
        """
        try:
            self.__validate_id()
            self.__find_vote()

        except Exception as error:
            self.VoteDisplay.setText(str(error))
            self.VoteDisplay.setStyleSheet(self.ERROR_COLOR)

        else:
            last_vote = self.__find_vote()

            # update who a candidate voted for.
            self.__get_voter_data().update({self.__get_id() : last_vote})
            # increases the amount of votes that a chosen candidate has.
            self.__get_candidates().update({self.__find_vote() :
                            self.__get_candidates().get(self.__find_vote(), self.DEFAULT_VOTES) + 1})

            self.VoteDisplay.setText("Submitted Vote.")
            self.VoteDisplay.setStyleSheet(self.GOOD_COLOR)

    def __cancel_voting(self) -> None:
        """
        Terminates the voting process, clears inputs boxes and radios.
        """
        self.VoteDisplay.clear()
        self.IDInput.clear()
        self.stackedWidget.setCurrentIndex(self.SETUP_WINDOW_INDEX)

        self.__set_candidates("")
        self.__set_voter_data({})

        for radio in self.VotePage.findChildren(QRadioButton): # delete all candidate radio buttons.
            radio.deleteLater()

    def __save_results(self) -> None:
        """
        Writes voting results to CSV files. Saves voter IDs and who they voted for, as well as candidate vote sums.
        """
        if not os.path.exists("voters.csv"):
            file = open("voters.csv", "w", newline="")
            writer = csv.writer(file)
            writer.writerow(["Voter ID", "Choice"])
            file.close()

        with open("voters.csv", "a+", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["NEW BALLOT", "-----"])

            for vote_id in self.__get_voter_data():
                data = [vote_id, self.__get_voter_data().get(vote_id)]
                writer.writerow(data)

        if not os.path.exists("candidates.csv"):
            file = open("candidates.csv", "w", newline="")
            writer = csv.writer(file)
            writer.writerow(["Candidate", "Votes"])
            file.close()

        with open("candidates.csv", "a+", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["NEW BALLOT", "-----"])

            for candidate in self.__get_candidates():
                print(candidate)
                data = [candidate, self.__get_candidates().get(candidate)]
                writer.writerow(data)

        self.VoteDisplay.setText("Results saved to CSV files (named voters.csv and candidates.csv)!")
        self.VoteDisplay.setStyleSheet(self.GOOD_COLOR)

    def __find_vote(self) -> str:
        """
        Finds and returns who the last voter voted for.
        """
        for radio in self.VotePage.findChildren(QRadioButton):
            if radio.isChecked():
                return radio.text()

        raise ValueError("Please enter a vote.")

    def __validate_candidate_count(self, temp_candidates) -> None:
        """
        Assures that the user entered the correct amount of candidates.
        """
        expected_count = self.CandidateCount.value()
        actual_count = len(temp_candidates)

        # user elects to enter candidate names - assure correct number of names.
        if actual_count != expected_count or actual_count > self.MAXIMUM_CANDIDATES:
            raise ValueError(f"Please enter {expected_count} or {self.MINIMUM_NAMES} candidate names.")

    def __validate_id(self) -> None:
        """
        Ensures that the user entered a valid, unique ID.
        """
        self.__set_id(self.IDInput.text())

        if self.__get_id() == "":
            raise ValueError("Please provide a voter ID.")

        elif not self.__get_id().isdigit():
            raise ValueError("Voter ID must only contain numbers (0-9).")

        elif self.__get_id() in self.__get_voter_data():  # voter ID already exists.
            raise ValueError("Please provide a unique voter ID.")

    def __set_candidates(self, new_candidates : str) -> None:
        """
        Converts new_candidates into a valid list, sets the transformed value to self.candidates
        :param new_candidates: String list of candidate names
        """
        self.__candidates = {}
        new_candidates = new_candidates.strip()

        if new_candidates == "": # user did not provide candidate names, provide empty list.
            for x in range(self.CandidateCount.value()):
                self.__candidates.update({f"Candidate {x + 1}" : self.DEFAULT_VOTES})

        else: # user specified a quantity of candidates.
            temp_candidates = new_candidates.split(",")
            self.__validate_candidate_count(temp_candidates) # first, check that the user entered the correct amount of candidates.

            for x in range(self.CandidateCount.value()):
                actual_name = temp_candidates[x].strip()
                curr_candidate = f"Candidate {actual_name}"

                if self.__get_candidates().get(curr_candidate) == self.DEFAULT_VOTES:
                    raise ValueError("All candidate names must be unique.")

                elif len(actual_name) > self.MAX_NAME_LENGTH:
                    raise ValueError(f"Each candidate name cannot be more than {self.MAX_NAME_LENGTH} characters.")

                elif actual_name == "":
                    raise ValueError("All candidates must have at least one character in their name.")

                self.__candidates.update({curr_candidate : self.DEFAULT_VOTES})

    def __set_id(self, new_id : str) -> None:
        """
        Sets the voter_id value to new_id.
        :param new_id: A provided voter ID.
        """
        self.__voter_id = new_id.strip()

    def __set_voter_data(self, new_data : dict[str, str]) -> None:
        """
        Sets voter data to new_data
        :param new_data: A new dictionary.
        """
        self.__voter_data = {}

    def __get_candidates(self) -> dict[str, int]:
        """
        Returns the current list of candidates.
        """
        return self.__candidates
    
    def __get_voter_data(self) -> dict[str, str]:
        """
        Returns voter_data list.
        """
        return self.__voter_data

    def __get_id(self) -> str:
        """
        Returns the current voter ID.
        """
        return self.__voter_id
