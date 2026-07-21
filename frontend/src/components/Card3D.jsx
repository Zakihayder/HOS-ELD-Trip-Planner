import { forwardRef } from "react";

const Card3D = forwardRef(function Card3D(
  { as: Component = "div", className = "", elevation = "rest", children, ...props },
  ref,
) {
  return (
    <Component
      ref={ref}
      className={`card-3d ${className}`.trim()}
      data-elevation={elevation}
      {...props}
    >
      {children}
    </Component>
  );
});

export default Card3D;