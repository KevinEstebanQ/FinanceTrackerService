#! /bin/bash
echo "what do you wish to do?"
echo "1" "Run the application"
echo "2 install dependencies"
read -p "Enter your choice: " choice

if  [[ -z "$choice" ]]; then
    echo "No choice entered. Please enter 1 or 2."
    exit 1
fi

if [[ "$choice" != "1" &&  "$choice" != "2" ]]; then
    echo "Invalid choice. Please enter 1 or 2."
    exit 1
fi

activate_env() {
    if [[ -d ".venv" ]]; then
        source .venv/bin/activate
    else
        echo "No virtual environment found. Please run 'python -m venv .venv' to create one."
        exit 1
    fi
}

install_dependencies() {
    activate_env
    pip install -r requirements.txt
}


if [[ "$choice" == "1" ]]; then
    activate_env
    uvicorn app.main:app --reload
elif [[ "$choice" == "2" ]]; then
    install_dependencies
else
    echo "Invalid choice. Please enter 1 or 2."
fi



