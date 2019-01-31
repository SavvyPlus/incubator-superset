/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
(function (global, factory) {
  if (typeof define === 'function' && define.amd) {
    define(['exports', 'react', 'prop-types', '../lib/String'], factory);
  } else if (typeof exports !== 'undefined') {
    factory(exports, require('react'), require('prop-types'), require('../lib/String'));
  } else {
    const mod = {
      exports: {},
    };
    factory(mod.exports, global.react, global.propTypes, global.String);
    global.Marker = mod.exports;
  }
}(this, function (exports, _react, _propTypes, _String) {


  Object.defineProperty(exports, '__esModule', {
    value: true,
  });
  exports.Marker = undefined;

  const _react2 = _interopRequireDefault(_react);

  const _propTypes2 = _interopRequireDefault(_propTypes);

  function _interopRequireDefault(obj) {
    return obj && obj.__esModule ? obj : {
      default: obj,
    };
  }

  const _extends = Object.assign || function (target) {
    for (let i = 1; i < arguments.length; i++) {
      const source = arguments[i];

      for (const key in source) {
        if (Object.prototype.hasOwnProperty.call(source, key)) {
          target[key] = source[key];
        }
      }
    }

    return target;
  };

  function _objectWithoutProperties(obj, keys) {
    const target = {};

    for (const i in obj) {
      if (keys.indexOf(i) >= 0) continue;
      if (!Object.prototype.hasOwnProperty.call(obj, i)) continue;
      target[i] = obj[i];
    }

    return target;
  }

  function _classCallCheck(instance, Constructor) {
    if (!(instance instanceof Constructor)) {
      throw new TypeError('Cannot call a class as a function');
    }
  }

  const _createClass = (function () {
    function defineProperties(target, props) {
      for (let i = 0; i < props.length; i++) {
        let descriptor = props[i];
        descriptor.enumerable = descriptor.enumerable || false;
        descriptor.configurable = true;
        if ('value' in descriptor) descriptor.writable = true;
        Object.defineProperty(target, descriptor.key, descriptor);
      }
    }

    return function (Constructor, protoProps, staticProps) {
      if (protoProps) defineProperties(Constructor.prototype, protoProps);
      if (staticProps) defineProperties(Constructor, staticProps);
      return Constructor;
    };
  }());

  function _possibleConstructorReturn(self, call) {
    if (!self) {
      throw new ReferenceError("this hasn't been initialised - super() hasn't been called");
    }

    return call && (typeof call === 'object' || typeof call === 'function') ? call : self;
  }

  function _inherits(subClass, superClass) {
    if (typeof superClass !== 'function' && superClass !== null) {
      throw new TypeError('Super expression must either be null or a function, not ' + typeof superClass);
    }

    subClass.prototype = Object.create(superClass && superClass.prototype, {
      constructor: {
        value: subClass,
        enumerable: false,
        writable: true,
        configurable: true,
      },
    });
    if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass;
  }

  const evtNames = ['click', 'dblclick', 'dragend', 'mousedown', 'mouseout', 'mouseover', 'mouseup', 'recenter'];

  const wrappedPromise = function wrappedPromise() {
    let wrappedPromise = {},
        promise = new Promise(function (resolve, reject) {
      wrappedPromise.resolve = resolve;
      wrappedPromise.reject = reject;
    });
    wrappedPromise.then = promise.then.bind(promise);
    wrappedPromise.catch = promise.catch.bind(promise);
    wrappedPromise.promise = promise;

    return wrappedPromise;
  };

  const Marker = exports.Marker = (function (_React$Component) {
    _inherits(Marker, _React$Component);

    function Marker() {
      _classCallCheck(this, Marker);

      return _possibleConstructorReturn(this, (Marker.__proto__ ||
              Object.getPrototypeOf(Marker)).apply(this, arguments));
    }

    _createClass(Marker, [{
      key: 'componentDidMount',
      value: function componentDidMount() {
        this.markerPromise = wrappedPromise();
        this.renderMarker();
      },
    }, {
      key: 'componentDidUpdate',
      value: function componentDidUpdate(prevProps) {
        if (this.props.map !== prevProps.map || this.props.position !== prevProps.position
            || this.props.icon !== prevProps.icon) {
          if (this.marker) {
            this.marker.setMap(null);
          }
          this.renderMarker();
        }
      },
    }, {
      key: 'componentWillUnmount',
      value: function componentWillUnmount() {
        if (this.marker) {
          this.marker.setMap(null);
        }
      },
    }, {
      key: 'renderMarker',
      value: function renderMarker() {
        let _this2 = this;

        let _props = this.props,
            map = _props.map,
            google = _props.google,
            position = _props.position,
            mapCenter = _props.mapCenter,
            icon = _props.icon,
            label = _props.label,
            draggable = _props.draggable,
            title = _props.title,
            props = _objectWithoutProperties(_props, ['map', 'google', 'position', 'mapCenter', 'icon', 'label', 'draggable', 'title']);

        if (!google) {
          return null;
        }

        let pos = position || mapCenter;
        if (!(pos instanceof google.maps.LatLng)) {
          pos = new google.maps.LatLng(pos.lat, pos.lng);
        }

        let pref = _extends({
          map,
          position: pos,
          icon,
          label,
          title,
          draggable,
        }, props);
        this.marker = new google.maps.Marker(pref);

        evtNames.forEach(function (e) {
          _this2.marker.addListener(e, _this2.handleEvent(e));
        });

        this.markerPromise.resolve(this.marker);
      },
    }, {
      key: 'getMarker',
      value: function getMarker() {
        return this.markerPromise;
      },
    }, {
      key: 'handleEvent',
      value: function handleEvent(evt) {
        let _this3 = this;

        return function (e) {
          let evtName = 'on' + (0, _String.camelize)(evt);
          if (_this3.props[evtName]) {
            _this3.props[evtName](_this3.props, _this3.marker, e);
          }
        };
      },
    }, {
      key: 'render',
      value: function render() {
        return null;
      },
    }]);

    return Marker;
  }(_react2.default.Component));

  Marker.propTypes = {
    position: _propTypes2.default.object,
    map: _propTypes2.default.object,
  };

  evtNames.forEach(function (e) {
    return Marker.propTypes[e] = _propTypes2.default.func;
  });

  Marker.defaultProps = {
    name: 'Marker',
  };

  exports.default = Marker;
}));
