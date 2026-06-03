package main

import (
	"fmt"
	"os"

	"standup"
)

func main() {
	if err := standup.Run(os.Args[1:], os.Stdin, os.Stdout); err != nil {
		fmt.Fprintln(os.Stderr, "standup-collect:", err)
		os.Exit(1)
	}
}
