# Create README Command

Generate a comprehensive README.md file following the template structure and CLAUDE Code guidelines.

## Usage

```
/create-readme [project-name]
```

## Initial Response

When this command is invoked:

1. **Check if parameters were provided**:
   - If a project name was provided as a parameter, use it as the default project name
   - Begin the interactive README generation process

2. **If no parameters provided**, respond with:
```
I'll help you create a comprehensive README.md file following the tackle template structure and CLAUDE Code guidelines.

Let's start by gathering some information about your project:

**Project Identity:**
1. Project name:
2. One-line description/tagline:
3. GitHub organization/username:
4. Repository name:
5. Go package name:
6. Package version (e.g., "v1"):

Please provide these details and I'll generate your README.md file.

Tip: You can also invoke this command with a project name directly: `/create-readme my-awesome-lib`
```

## Implementation Instructions

After gathering the basic project information, follow these steps:

### Step 1: Gather Complete Project Information

Ask for the following information in an organized manner:

#### **Project Identity & Branding**
- Project name
- ASCII art preference (generate automatically or skip)
- One-line tagline description
- GitHub organization/username
- Repository name
- Go package name
- Package version

#### **Philosophy & Positioning**
- Target audience description
- 4 key features to highlight
- Primary use cases
- What makes this project special/different

#### **Technical Details**
- Main client/API configuration fields
- Primary usage example (the most common use case)
- Core features (3-4 main capabilities with descriptions)
- API sections to document
- Error types used in the project
- Testing approach (mock servers, standard testing, etc.)

#### **Project Metadata**
- Current project status (early development, production ready, etc.)
- API compatibility notes
- Author name and URL
- Project website/links
- API documentation links

### Step 2: Generate ASCII Art (if requested)

If ASCII art is requested, generate appropriate ASCII art for the project name using a clean, readable style similar to:

```
    ____        __    __              ____
   / __ \__  __/ /_  / /__  _____    / __ \____
  / /_/ / / / / __ \/ / _ \/ ___/   / / / / __ \
 / ____/ /_/ / /_/ / /  __/ /  _   / /_/ / /_/ /
/_/    \__,_/_.___/_/\___/_/  (_)  \____/\____/
```

### Step 3: Generate README Content

Create a comprehensive README.md file with the following structure:

```markdown
# {project-name}

{ascii-art-if-requested}

{tagline-description}

{badges-section}

## Philosophy

{project-name} is designed {target-audience-description}. This library emphasizes:

- **Zero external dependencies** (except test libraries)
- **{key-feature-1}** with {benefit-1}
- **{key-feature-2}** through {implementation-detail}
- **{key-feature-3}** for {use-case}
- **{key-feature-4}** {additional-benefit}

Perfect for {primary-use-cases} without complex dependency reviews.

## Installation

```bash
go get github.com/{github-org}/{repo-name}/{version}
```

## Quick Start

{quick-start-example}

## Core Features

{core-features-with-examples}

## API Operations

{api-sections-with-examples}

## Error Handling

{error-handling-examples}

## Testing

{testing-examples}

## Project Status

{project-status-description}

## Development

This project was written entirely by [Claude Code AI](https://claude.ai/code), under the direction of [{author-name}]({author-url}) following the detailed implementation plans found in the [`plans/`](./plans/) directory. The plans document the complete development process, architecture decisions, and feature implementation strategy.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on how to get involved.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## Links

{project-links}
```

### Step 4: Follow CLAUDE Code Guidelines

Ensure all code examples follow these guidelines:

1. **Inline single-use variables** - Don't create variables that are only used once
2. **Keep multi-use variables** - Variables referenced multiple times should be declared separately
3. **Use realistic examples** - Show actual, working code patterns
4. **Include error handling** - Always show proper error handling
5. **Add meaningful comments** - Explain what the code does
6. **Show context usage** - Demonstrate context.Context support

### Step 5: Code Example Patterns

Use these patterns for code examples:

#### **Good Pattern (inline single-use variables):**
```go
var resp SomeResponse
err := client.DoSomething(ctx, SomeRequest{
    Field: "value",
}, &resp)
```

#### **Bad Pattern (unnecessary variable):**
```go
req := SomeRequest{Field: "value"}
err := client.DoSomething(ctx, req, &resp)
```

#### **Multi-use variables (keep separate):**
```go
var resp SomeResponse
err := client.DoSomething(ctx, request, &resp)
if err != nil {
    log.Fatal(err)
}
fmt.Printf("Result: %s", resp.JobID) // resp used again
```

### Step 6: Generate Badges

Always include these badges (customize URLs):
```markdown
[![Go Version](https://img.shields.io/github/go-mod/go-version/{github-org}/{repo-name})](https://golang.org/dl/)
[![CI Status](https://github.com/{github-org}/{repo-name}/workflows/CI/badge.svg)](https://github.com/{github-org}/{repo-name}/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Go Report Card](https://goreportcard.com/badge/github.com/{github-org}/{repo-name})](https://goreportcard.com/report/github.com/{github-org}/{repo-name})
```

### Step 7: Validation and Final Steps

1. **Verify all placeholders are filled**
2. **Check code examples compile** (conceptually)
3. **Ensure examples follow CLAUDE guidelines**
4. **Include appropriate sections** for the project type
5. **Write the README.md file** to the project root
6. **Offer to create CONTRIBUTING.md** if it doesn't exist

### Step 8: Additional Suggestions

After creating the README, offer to:
1. Create a CONTRIBUTING.md file if it doesn't exist
2. Review existing code examples in the project for consistency
3. Generate additional documentation files if needed
4. Update package documentation to match the README

## Error Handling

If information is missing or unclear:
1. **Ask specific follow-up questions**
2. **Provide examples** of what you're looking for
3. **Make reasonable assumptions** based on common Go patterns
4. **Clearly indicate assumptions** made in the generated content

## Quality Standards

The generated README should:
- **Be comprehensive** but not overwhelming
- **Follow the tackle template structure**
- **Include realistic, working code examples**
- **Demonstrate all major features**
- **Be maintainable** and easy to update
- **Follow CLAUDE Code guidelines** consistently
- **Be professional** and well-organized

## Final Notes

This command generates production-ready README files that:
- Match the quality of tackle and publer.go READMEs
- Follow established Go community conventions
- Include comprehensive examples and documentation
- Are immediately usable for open source projects
- Maintain consistency across projects
