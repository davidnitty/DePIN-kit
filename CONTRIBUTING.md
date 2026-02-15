# Contributing to IoTeX DePIN Kit

Thank you for your interest in contributing! We welcome contributions from everyone.

## 🤝 How to Contribute

### Reporting Bugs

1. Check existing issues first
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python/Node versions)

### Suggesting Features

1. Check if feature already exists or is planned
2. Create a feature request with:
   - Use case description
   - Proposed implementation (if known)
   - Potential impact

### Submitting Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit your changes: `git commit -m 'Add my feature'`
7. Push to branch: `git push origin feature/my-feature`
8. Open a Pull Request

## 📝 Code Style

### Python

- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for functions and classes
- Maximum line length: 100 characters

Example:
```python
def calculate_rewards(device_id: int, metrics: List[Dict]) -> float:
    """
    Calculate rewards for a device based on metrics.

    Args:
        device_id: Device ID
        metrics: List of metric dictionaries

    Returns:
        Calculated reward amount
    """
    pass
```

### Solidity

- Follow Solidity style guide
- Use NatSpec comments for functions
- Maximum line length: 120 characters

Example:
```solidity
/**
 * @dev Register a new device
 * @param metadataURI IPFS hash of device metadata
 * @return deviceId ID of registered device
 */
function registerDevice(string memory metadataURI)
    external
    returns (uint256 deviceId)
{
    // implementation
}
```

### JavaScript/React

- Use ES6+ syntax
- Functional components with hooks
- PropTypes or TypeScript for type checking
- Clear component and function names

Example:
```javascript
/**
 * Device card component
 * @param {Object} device - Device information
 */
const DeviceCard = ({ device }) => {
  return (
    <div className="device-card">
      <h3>{device.name}</h3>
    </div>
  );
};
```

## 🧪 Testing

### Python Tests

```bash
cd backend
pytest
```

### JavaScript Tests

```bash
cd contracts
npm test
```

```bash
cd frontend
npm test
```

### Test Coverage

- Aim for >80% code coverage
- Include edge cases and error conditions
- Mock external dependencies

## 📖 Documentation

- Update README for user-facing changes
- Add docstrings to new functions
- Update API documentation
- Comment complex logic

## 🎯 Pull Request Guidelines

### PR Title

Use a clear, descriptive title:
- ✅ "Add device registration API endpoint"
- ✅ "Fix reward calculation bug"
- ❌ "Update files"
- ❌ "WIP"

### PR Description

Include:
- What was changed and why
- How it was tested
- Screenshots (for UI changes)
- Breaking changes (if any)
- Related issues

### Review Process

1. Automated checks must pass
2. Code review by maintainers
3. Address review feedback
4. Approval required to merge

## 🚀 Release Process

1. Update version numbers
2. Update CHANGELOG
3. Tag release
4. Create GitHub release
5. Deploy to production

## 🎨 Project Structure

```
iotex-depin-kit/
├── contracts/          # Smart contracts
├── backend/           # Python API
├── frontend/          # React UI
└── docs/             # Documentation
```

## 🔒 Security

- Never commit private keys or secrets
- Use environment variables
- Report security vulnerabilities privately
- Follow OWASP guidelines

## 💬 Communication

- Be respectful and constructive
- Ask questions if unsure
- Help other contributors
- Share knowledge

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to IoTeX DePIN Kit! 🙏
